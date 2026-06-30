"""Baseline biomedical NER extraction pipeline."""

from __future__ import annotations

import argparse
import logging
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from tqdm import tqdm

from gbmbert.annotation.schema import Paper
from gbmbert.extraction.entities import EntityExtractionResult, entity_from_model_output
from gbmbert.extraction.io import load_pubmed_jsonl, save_entity_jsonl
from gbmbert.preprocess.clean_text import clean_text

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "d4data/biomedical-ner-all"
DEFAULT_MAX_CHUNK_WORDS = 250
DEFAULT_CHUNK_OVERLAP_WORDS = 40
NERPipeline = Callable[[str], list[dict[str, Any]]]
TextChunk = tuple[int, str]
_WORD_RE = re.compile(r"\S+")


class BiomedicalNERPipeline:
    """Run baseline biomedical NER over PubMed paper records."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        ner_pipeline: NERPipeline | None = None,
        device: int = -1,
        max_chunk_words: int = DEFAULT_MAX_CHUNK_WORDS,
        chunk_overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
    ) -> None:
        if max_chunk_words < 1:
            raise ValueError("max_chunk_words must be at least 1")
        if chunk_overlap_words < 0:
            raise ValueError("chunk_overlap_words must not be negative")
        if chunk_overlap_words >= max_chunk_words:
            raise ValueError("chunk_overlap_words must be less than max_chunk_words")

        self.model_name = model_name
        self.device = device
        self._ner_pipeline = ner_pipeline
        self.max_chunk_words = max_chunk_words
        self.chunk_overlap_words = chunk_overlap_words

    @property
    def ner_pipeline(self) -> NERPipeline:
        if self._ner_pipeline is None:
            self._ner_pipeline = create_ner_pipeline(self.model_name, self.device)
        return self._ner_pipeline

    def extract_from_paper(self, paper: Paper) -> EntityExtractionResult:
        """Extract entities from a validated PubMed paper."""

        source_text = paper_to_source_text(paper)
        if not source_text:
            return EntityExtractionResult(pmid=paper.pmid, entities=[])

        entities_by_span = {}
        for chunk_start, chunk_text in split_text_chunks(
            source_text,
            max_words=self.max_chunk_words,
            overlap_words=self.chunk_overlap_words,
        ):
            outputs = self.ner_pipeline(chunk_text)
            for output in outputs:
                entity = entity_from_model_output(
                    offset_model_output(output, chunk_start),
                    source_text,
                )
                key = (entity.start, entity.end, entity.label, entity.normalized_text)
                existing_entity = entities_by_span.get(key)
                if existing_entity is None or entity.confidence > existing_entity.confidence:
                    entities_by_span[key] = entity

        entities = sorted(entities_by_span.values(), key=lambda entity: (entity.start, entity.end))
        return EntityExtractionResult(pmid=paper.pmid, entities=entities)

    def extract_many(self, papers: Iterable[Paper]) -> Iterable[EntityExtractionResult]:
        """Yield entity extraction results for many papers."""

        for paper in papers:
            yield self.extract_from_paper(paper)


def create_ner_pipeline(model_name: str = DEFAULT_MODEL_NAME, device: int = -1) -> NERPipeline:
    """Create the Hugging Face NER pipeline lazily."""

    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError(
            "transformers is required for NER extraction. Install the project dependencies first."
        ) from exc

    return pipeline(
        "ner",
        model=model_name,
        tokenizer=model_name,
        aggregation_strategy="simple",
        device=device,
    )


def paper_to_source_text(paper: Paper) -> str:
    """Combine title and abstract into the source text used for NER offsets."""

    return clean_text("\n\n".join(part for part in [paper.title, paper.abstract] if part))


def split_text_chunks(
    text: str,
    max_words: int = DEFAULT_MAX_CHUNK_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> Iterable[TextChunk]:
    """Yield source-text chunks with their original character offsets."""

    if max_words < 1:
        raise ValueError("max_words must be at least 1")
    if overlap_words < 0:
        raise ValueError("overlap_words must not be negative")
    if overlap_words >= max_words:
        raise ValueError("overlap_words must be less than max_words")

    word_matches = list(_WORD_RE.finditer(text))
    if len(word_matches) <= max_words:
        yield 0, text
        return

    step_words = max_words - overlap_words
    for word_start in range(0, len(word_matches), step_words):
        word_end = min(word_start + max_words, len(word_matches))
        chunk_start = word_matches[word_start].start()
        chunk_end = word_matches[word_end - 1].end()
        yield chunk_start, text[chunk_start:chunk_end]
        if word_end == len(word_matches):
            break


def offset_model_output(output: dict[str, Any], offset: int) -> dict[str, Any]:
    """Convert chunk-local model offsets back to source-text offsets."""

    adjusted_output = dict(output)
    for offset_key in ("start", "end"):
        if adjusted_output.get(offset_key) is not None:
            adjusted_output[offset_key] = int(adjusted_output[offset_key]) + offset
    return adjusted_output


def run_extraction(
    input_path: str | Path,
    output_path: str | Path,
    model_name: str = DEFAULT_MODEL_NAME,
    device: int = -1,
    max_chunk_words: int = DEFAULT_MAX_CHUNK_WORDS,
    chunk_overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> Path:
    """Load PubMed JSONL, run NER, and write entity JSONL output."""

    extractor = BiomedicalNERPipeline(
        model_name=model_name,
        device=device,
        max_chunk_words=max_chunk_words,
        chunk_overlap_words=chunk_overlap_words,
    )
    papers = load_pubmed_jsonl(input_path)
    LOGGER.info("Loading PubMed records from %s", input_path)
    results = (
        extractor.extract_from_paper(paper)
        for paper in tqdm(papers, desc="Extracting entities", unit="paper")
    )
    return save_entity_jsonl(results, output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract biomedical entities from PubMed JSONL.")
    parser.add_argument("input", type=Path, help="Input PubMed JSONL path.")
    parser.add_argument("output", type=Path, help="Output entity JSONL path.")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Hugging Face NER model name.")
    parser.add_argument("--device", type=int, default=-1, help="Transformers device id; use -1 for CPU.")
    parser.add_argument(
        "--max-chunk-words",
        type=int,
        default=DEFAULT_MAX_CHUNK_WORDS,
        help="Maximum words sent to the NER model per chunk.",
    )
    parser.add_argument(
        "--chunk-overlap-words",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP_WORDS,
        help="Words repeated between adjacent chunks to catch boundary entities.",
    )
    parser.add_argument("--log-level", default="INFO", help="Python logging level.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    output_path = run_extraction(
        input_path=args.input,
        output_path=args.output,
        model_name=args.model,
        device=args.device,
        max_chunk_words=args.max_chunk_words,
        chunk_overlap_words=args.chunk_overlap_words,
    )
    LOGGER.info("Saved entity extraction output to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
