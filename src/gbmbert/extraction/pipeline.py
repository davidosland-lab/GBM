"""Baseline biomedical NER extraction pipeline."""

from __future__ import annotations

import argparse
import logging
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
NERPipeline = Callable[[str], list[dict[str, Any]]]


class BiomedicalNERPipeline:
    """Run baseline biomedical NER over PubMed paper records."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        ner_pipeline: NERPipeline | None = None,
        device: int = -1,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._ner_pipeline = ner_pipeline

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

        outputs = self.ner_pipeline(source_text)
        entities = [entity_from_model_output(output, source_text) for output in outputs]
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


def run_extraction(
    input_path: str | Path,
    output_path: str | Path,
    model_name: str = DEFAULT_MODEL_NAME,
    device: int = -1,
) -> Path:
    """Load PubMed JSONL, run NER, and write entity JSONL output."""

    extractor = BiomedicalNERPipeline(model_name=model_name, device=device)
    papers = list(load_pubmed_jsonl(input_path))
    LOGGER.info("Loaded %d PubMed records from %s", len(papers), input_path)
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
    )
    LOGGER.info("Saved entity extraction output to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
