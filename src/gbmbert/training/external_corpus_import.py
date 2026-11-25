"""External biomedical corpus ingestion adapter (PR163/PR164).

Re-founds the NER/relation tracks on real, peer-used annotated corpora instead
of synthetic fixtures. A corpus-agnostic pipeline:

    raw corpus --(reader)--> [CorpusDocument] --(crosswalk)--> project gold_entities
                                                              (+ optional gold_relations)

Each corpus gets a reader (raw format -> normalized CorpusDocument) plus a block
in ``configs/extraction/external_corpus_crosswalk.json`` mapping its label scheme
onto the stable project labels (DRUG/DISEASE/GENE/CELL_TYPE/...). Onboarding a new
corpus is a new reader + config block; the project label scheme never changes.

Corpora:
- BC5CDR via the token-level ``tner/bc5cdr`` mirror (Chemical+Disease NER; no PMIDs/relations).
- BioRED via NCBI BioC JSON (PMIDs, character offsets, 6 entity types, document-level relations).
- EBM-NLP (Nye et al., ACL 2018) aggregated starting spans: Intervention → TREATMENT, Outcome → OUTCOME.
- ``treatment_stub`` JSONL fixture reader kept as a smoke-path for Intervention/Procedure → TREATMENT.

Observe-only, research-use only. Imported rows are tagged with corpus provenance so
the governance/authenticity tooling can tell real-corpus data from fixtures. This
does not promote a dataset or claim a validated GBM-BERT model exists.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from gbmbert.datasets import RESEARCH_WARNING

DEFAULT_CROSSWALK = Path("configs/extraction/external_corpus_crosswalk.json")
EXTERNAL_SOURCE_TYPE = "external_corpus"

# EBM-NLP aggregated starting_spans: non-zero token labels mark P/I/O spans.
_EBM_STARTING_SPAN_ELEMENTS: dict[str, str] = {
    "interventions": "Intervention",
    "outcomes": "Outcome",
}

# BC5CDR token-level mirror (tner/bc5cdr) tag scheme.
_BC5CDR_TAGS: dict[int, tuple[str, str]] = {
    1: ("B", "Chemical"),
    2: ("B", "Disease"),
    3: ("I", "Disease"),
    4: ("I", "Chemical"),
}


@dataclass(frozen=True)
class CorpusEntity:
    text: str
    label: str  # source-corpus label, before crosswalk
    start: int
    end: int
    identifier: str = ""


@dataclass(frozen=True)
class CorpusRelation:
    relation_type: str  # source-corpus relation label, before crosswalk
    head_identifier: str
    tail_identifier: str
    novelty: str = ""


@dataclass
class CorpusDocument:
    doc_id: str
    text: str
    entities: list[CorpusEntity] = field(default_factory=list)
    relations: list[CorpusRelation] = field(default_factory=list)
    source_pmid: str | None = None


@dataclass(frozen=True)
class ExternalCorpusImportReport:
    corpus: str
    reader: str
    input_path: str
    output_path: str
    relations_output_path: str
    license: str
    document_count: int
    entity_count: int
    relation_count: int
    project_entity_label_counts: dict[str, int]
    project_relation_label_counts: dict[str, int]
    dropped_entity_label_counts: dict[str, int]
    dropped_relation_label_counts: dict[str, int]
    source_type: str
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------------------ readers


def read_bc5cdr_tner(path: str | Path) -> list[CorpusDocument]:
    """Read the token-level ``tner/bc5cdr`` JSONL (one {tags, tokens} object per line).

    Each line is treated as one document; spans are reconstructed from BIO tags and
    character offsets are computed against a single-space token join.
    """

    documents: list[CorpusDocument] = []
    for index, row in enumerate(_read_jsonl(path)):
        tokens = [str(tok) for tok in (row.get("tokens") or [])]
        tags = [int(tag) for tag in (row.get("tags") or [])]
        if len(tokens) != len(tags):
            raise ValueError(f"tokens/tags length mismatch on document {index} in {path}")
        text, offsets = _join_tokens(tokens)
        entities = _spans_from_bio(tokens, tags, offsets, text)
        documents.append(CorpusDocument(doc_id=f"bc5cdr-{index}", text=text, entities=entities))
    return documents


def read_biored_bioc(path: str | Path) -> list[CorpusDocument]:
    """Read NCBI BioRED BioC JSON (single file or directory of ``*.BioC.JSON`` files).

    Document ``id`` is the PubMed PMID. Entity offsets are absolute character offsets
    against the reconstructed passage buffer. Relations are document-level and keyed
    by entity identifiers (not mention ids).
    """

    paths = _resolve_bioc_json_paths(path)
    documents: list[CorpusDocument] = []
    for bioc_path in paths:
        payload = _read_json(bioc_path)
        raw_docs = payload.get("documents") if isinstance(payload, dict) else None
        if not isinstance(raw_docs, list):
            raise ValueError(f"BioC JSON must contain a documents list: {bioc_path}")
        for raw in raw_docs:
            documents.append(_parse_biored_document(raw, source_path=bioc_path))
    return documents


def _resolve_bioc_json_paths(path: str | Path) -> list[Path]:
    root = Path(path)
    if root.is_file():
        return [root]
    if root.is_dir():
        # Deduplicate: Windows case-insensitive FS makes *.BioC.JSON and *.bioc.json overlap.
        found = {p.resolve(): p for p in root.glob("*.BioC.JSON")}
        found.update({p.resolve(): p for p in root.glob("*.bioc.json")})
        paths = sorted(found.values(), key=lambda item: item.name.lower())
        if not paths:
            found = {p.resolve(): p for p in root.rglob("*.BioC.JSON")}
            paths = sorted(found.values(), key=lambda item: str(item).lower())
        if not paths:
            raise ValueError(f"no *.BioC.JSON files found under {root}")
        return paths
    raise ValueError(f"BioRED BioC input not found: {root}")


def _parse_biored_document(raw: dict[str, Any], *, source_path: Path) -> CorpusDocument:
    doc_id = str(raw.get("id") or "").strip()
    if not doc_id:
        raise ValueError(f"BioC document missing id in {source_path}")
    passages = raw.get("passages") or []
    if not isinstance(passages, list):
        raise ValueError(f"BioC document {doc_id} passages must be a list")
    text = _bioc_reconstruct_text(passages)
    entities: list[CorpusEntity] = []
    for passage in passages:
        for annotation in passage.get("annotations") or []:
            entities.extend(_bioc_entities_from_annotation(annotation, text=text, doc_id=doc_id))
    relations = [_bioc_relation(rel, doc_id=doc_id) for rel in (raw.get("relations") or [])]
    pmid = doc_id if doc_id.isdigit() else None
    return CorpusDocument(
        doc_id=doc_id,
        text=text,
        entities=entities,
        relations=relations,
        source_pmid=pmid,
    )


def _bioc_reconstruct_text(passages: list[dict[str, Any]]) -> str:
    if not passages:
        return ""
    ends = [int(p.get("offset") or 0) + len(str(p.get("text") or "")) for p in passages]
    max_end = max(ends) if ends else 0
    buf = ["\0"] * max_end
    for passage in passages:
        offset = int(passage.get("offset") or 0)
        passage_text = str(passage.get("text") or "")
        for index, char in enumerate(passage_text):
            buf[offset + index] = char
    return "".join(" " if char == "\0" else char for char in buf)


def _bioc_entities_from_annotation(annotation: dict[str, Any], *, text: str, doc_id: str) -> list[CorpusEntity]:
    infons = annotation.get("infons") or {}
    label = str(infons.get("type") or "").strip()
    identifier = str(infons.get("identifier") or "").strip()
    mention = str(annotation.get("text") or "")
    entities: list[CorpusEntity] = []
    for location in annotation.get("locations") or []:
        start = int(location.get("offset") or 0)
        length = int(location.get("length") or 0)
        end = start + length
        span = text[start:end]
        if span != mention and mention:
            # Prefer the reconstructed span when offsets are authoritative.
            span_text = span if span else mention
        else:
            span_text = span or mention
        if not label or start < 0 or end < start:
            raise ValueError(f"invalid BioC annotation in document {doc_id}: {annotation!r}")
        entities.append(
            CorpusEntity(text=span_text, label=label, start=start, end=end, identifier=identifier)
        )
    return entities


def _bioc_relation(raw: dict[str, Any], *, doc_id: str) -> CorpusRelation:
    infons = raw.get("infons") or {}
    relation_type = str(infons.get("type") or "").strip()
    head = str(infons.get("entity1") or "").strip()
    tail = str(infons.get("entity2") or "").strip()
    if not relation_type or not head or not tail:
        raise ValueError(f"invalid BioC relation in document {doc_id}: {raw!r}")
    return CorpusRelation(
        relation_type=relation_type,
        head_identifier=head,
        tail_identifier=tail,
        novelty=str(infons.get("novel") or "").strip(),
    )


def read_treatment_stub_jsonl(path: str | Path) -> list[CorpusDocument]:
    """Read a stub intervention/procedure JSONL corpus into CorpusDocuments.

    Each line is ``{doc_id, text, pmid?, entities:[{text,label,start,end}]}``.
    Source labels such as ``Intervention`` / ``Procedure`` are crosswalked to
    project ``TREATMENT``. Observe-only research fixture path.
    """

    input_path = Path(path)
    documents: list[CorpusDocument] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {input_path}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number} of {input_path}")
            doc_id = str(row.get("doc_id") or row.get("pmid") or f"treatment-stub-{line_number}")
            text = str(row.get("text") or "")
            entities: list[CorpusEntity] = []
            for index, entity in enumerate(row.get("entities") or []):
                if not isinstance(entity, dict):
                    continue
                start = int(entity.get("start", -1))
                end = int(entity.get("end", -1))
                label = str(entity.get("label") or "").strip()
                mention = str(entity.get("text") or "")
                if not label or start < 0 or end <= start:
                    continue
                entities.append(
                    CorpusEntity(
                        text=mention or text[start:end],
                        label=label,
                        start=start,
                        end=end,
                        identifier=str(entity.get("identifier") or f"{doc_id}:{index}"),
                    )
                )
            documents.append(
                CorpusDocument(
                    doc_id=doc_id,
                    text=text,
                    entities=entities,
                    source_pmid=str(row.get("pmid") or "") or None,
                )
            )
    return documents


def read_ebm_nlp(path: str | Path) -> list[CorpusDocument]:
    """Read EBM-NLP aggregated starting-span annotations (Intervention + Outcome).

    ``path`` must be the corpus root containing ``documents/`` and
    ``annotations/aggregated/starting_spans/{interventions,outcomes}/``.
    Token labels are collapsed into character spans against a single-space token
    join (same convention as the upstream EBM-NLP demo). Participants are not
    loaded (no stable project label). Prefer ``test/gold`` over ``test/crowd``
    when both exist for a PMID.
    """

    root = Path(path)
    documents_dir = root / "documents"
    spans_root = root / "annotations" / "aggregated" / "starting_spans"
    if not documents_dir.is_dir() or not spans_root.is_dir():
        raise ValueError(
            f"EBM-NLP root must contain documents/ and annotations/aggregated/starting_spans/: {root}"
        )

    ann_by_pmid: dict[str, dict[str, Path]] = {}
    for element, source_label in _EBM_STARTING_SPAN_ELEMENTS.items():
        for ann_path in _iter_ebm_ann_files(spans_root / element):
            pmid = ann_path.name.split(".", 1)[0]
            chosen = ann_by_pmid.setdefault(pmid, {})
            prior = chosen.get(source_label)
            if prior is None or _ebm_ann_rank(ann_path) < _ebm_ann_rank(prior):
                chosen[source_label] = ann_path

    documents: list[CorpusDocument] = []
    for pmid in sorted(ann_by_pmid, key=lambda value: (len(value), value)):
        tokens_path = documents_dir / f"{pmid}.tokens"
        if not tokens_path.exists():
            continue
        tokens = [line for line in tokens_path.read_text(encoding="utf-8").splitlines() if line != ""]
        if not tokens:
            continue
        text, offsets = _join_tokens(tokens)
        entities: list[CorpusEntity] = []
        for source_label, ann_path in sorted(ann_by_pmid[pmid].items()):
            labels = _read_ebm_token_labels(ann_path)
            if len(labels) != len(tokens):
                raise ValueError(
                    f"token/label length mismatch for PMID {pmid} ({source_label}): "
                    f"{len(tokens)} tokens vs {len(labels)} labels in {ann_path}"
                )
            for index, (start_idx, end_idx) in enumerate(_condense_nonzero_spans(labels)):
                start = offsets[start_idx]
                end = offsets[end_idx - 1] + len(tokens[end_idx - 1])
                entities.append(
                    CorpusEntity(
                        text=text[start:end],
                        label=source_label,
                        start=start,
                        end=end,
                        identifier=f"{pmid}:{source_label}:{index}",
                    )
                )
        documents.append(
            CorpusDocument(doc_id=pmid, text=text, entities=entities, source_pmid=pmid)
        )
    return documents


def _iter_ebm_ann_files(element_dir: Path) -> Iterable[Path]:
    if not element_dir.is_dir():
        return []
    return sorted(element_dir.rglob("*.ann"))


def _ebm_ann_rank(path: Path) -> tuple[int, int, str]:
    """Lower rank wins: gold test > train aggregated > crowd test."""

    parts = {part.casefold() for part in path.parts}
    if "gold" in parts:
        split_rank = 0
    elif "crowd" in parts:
        split_rank = 2
    else:
        split_rank = 1
    return (split_rank, len(path.parts), str(path))


def _read_ebm_token_labels(path: Path) -> list[int]:
    labels: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        labels.append(int(line.strip()))
    return labels


def _condense_nonzero_spans(labels: list[int]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(labels):
        if labels[index] == 0:
            index += 1
            continue
        start = index
        index += 1
        while index < len(labels) and labels[index] != 0:
            index += 1
        spans.append((start, index))
    return spans


READERS: dict[str, Callable[[str | Path], list[CorpusDocument]]] = {
    "bc5cdr_tner": read_bc5cdr_tner,
    "biored_bioc": read_biored_bioc,
    "ebm_nlp": read_ebm_nlp,
    "treatment_stub_jsonl": read_treatment_stub_jsonl,
}


# -------------------------------------------------------------------------- import


def import_external_corpus(
    *,
    corpus: str,
    input_path: str | Path,
    output_path: str | Path,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
    relations_output_path: str | Path | None = None,
) -> ExternalCorpusImportReport:
    """Map an external corpus into project gold_entities JSONL via the label crosswalk."""

    crosswalk = _read_json(crosswalk_path)
    corpora = crosswalk.get("corpora") or {}
    if corpus not in corpora:
        raise ValueError(f"corpus '{corpus}' not in crosswalk {crosswalk_path}; known: {sorted(corpora)}")
    spec = corpora[corpus]
    reader_name = str(spec.get("reader") or "")
    if reader_name not in READERS:
        raise ValueError(f"no reader '{reader_name}' registered for corpus '{corpus}'; known: {sorted(READERS)}")
    entity_map = {str(k): str(v) for k, v in (spec.get("entity_label_map") or {}).items()}
    relation_map = {str(k): str(v) for k, v in (spec.get("relation_label_map") or {}).items()}
    license_text = str(spec.get("license") or "unspecified")

    documents = READERS[reader_name](input_path)

    project_entity_counts: dict[str, int] = {}
    project_relation_counts: dict[str, int] = {}
    dropped_entity_counts: dict[str, int] = {}
    dropped_relation_counts: dict[str, int] = {}
    entity_count = 0
    relation_count = 0
    records: list[dict[str, Any]] = []
    relation_records: list[dict[str, Any]] = []

    for document in documents:
        mapped_entities: list[dict[str, Any]] = []
        id_to_project: dict[str, tuple[str, str]] = {}
        for entity in document.entities:
            project_label = entity_map.get(entity.label)
            if project_label is None:
                dropped_entity_counts[entity.label] = dropped_entity_counts.get(entity.label, 0) + 1
                continue
            project_entity_counts[project_label] = project_entity_counts.get(project_label, 0) + 1
            entity_count += 1
            mapped_entities.append(
                {
                    "confidence": 1.0,
                    "end": entity.end,
                    "label": project_label,
                    "normalized_text": entity.text,
                    "start": entity.start,
                    "text": entity.text,
                }
            )
            if entity.identifier and entity.identifier not in id_to_project:
                id_to_project[entity.identifier] = (project_label, entity.text)

        for relation in document.relations:
            project_rel = relation_map.get(relation.relation_type)
            if project_rel is None:
                dropped_relation_counts[relation.relation_type] = (
                    dropped_relation_counts.get(relation.relation_type, 0) + 1
                )
                continue
            head = id_to_project.get(relation.head_identifier)
            tail = id_to_project.get(relation.tail_identifier)
            if head is None or tail is None:
                dropped_relation_counts[relation.relation_type] = (
                    dropped_relation_counts.get(relation.relation_type, 0) + 1
                )
                continue
            project_relation_counts[project_rel] = project_relation_counts.get(project_rel, 0) + 1
            relation_count += 1
            relation_records.append(
                {
                    "head": f"{head[0]}:{head[1]}",
                    "label": project_rel,
                    "novelty": relation.novelty,
                    "source_corpus": corpus,
                    "source_pmid": document.source_pmid or document.doc_id,
                    "source_type": EXTERNAL_SOURCE_TYPE,
                    "tail": f"{tail[0]}:{tail[1]}",
                    "task": "relation",
                    "text": document.text,
                    "warning": RESEARCH_WARNING,
                }
            )

        records.append(
            {
                "entities": mapped_entities,
                "pmid": document.source_pmid or document.doc_id,
                "source_corpus": corpus,
                "source_type": EXTERNAL_SOURCE_TYPE,
                "text": document.text,
            }
        )

    out_path = _write_jsonl(output_path, records)
    relations_path = ""
    if relations_output_path is not None:
        relations_path = str(_write_jsonl(relations_output_path, relation_records))
    elif relation_records:
        # Default beside the entities output when relations were mapped.
        default_rel = Path(output_path).with_name("gold_relations.jsonl")
        relations_path = str(_write_jsonl(default_rel, relation_records))

    warnings: list[str] = []
    if dropped_entity_counts:
        warnings.append(
            "dropped unmapped source entity labels (add them to the crosswalk to keep them): "
            + ", ".join(f"{label}={count}" for label, count in sorted(dropped_entity_counts.items()))
        )
    if dropped_relation_counts:
        warnings.append(
            "dropped unmapped or unresolved source relations: "
            + ", ".join(f"{label}={count}" for label, count in sorted(dropped_relation_counts.items()))
        )
    if not entity_count:
        warnings.append("no entities mapped; check the reader and crosswalk")

    return ExternalCorpusImportReport(
        corpus=corpus,
        reader=reader_name,
        input_path=str(Path(input_path)),
        output_path=str(out_path),
        relations_output_path=relations_path,
        license=license_text,
        document_count=len(documents),
        entity_count=entity_count,
        relation_count=relation_count,
        project_entity_label_counts=dict(sorted(project_entity_counts.items())),
        project_relation_label_counts=dict(sorted(project_relation_counts.items())),
        dropped_entity_label_counts=dict(sorted(dropped_entity_counts.items())),
        dropped_relation_label_counts=dict(sorted(dropped_relation_counts.items())),
        source_type=EXTERNAL_SOURCE_TYPE,
        warnings=warnings,
    )


# -------------------------------------------------------------------------- output


def save_external_corpus_import_json(report: ExternalCorpusImportReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return output


def save_external_corpus_import_markdown(report: ExternalCorpusImportReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(format_external_corpus_import_markdown(report), encoding="utf-8")
    return output


def format_external_corpus_import_markdown(report: ExternalCorpusImportReport) -> str:
    lines = [
        "# External Corpus Import",
        "",
        RESEARCH_WARNING,
        "",
        f"- Corpus: `{report.corpus}` (reader `{report.reader}`)",
        f"- License: {report.license}",
        f"- Source type: `{report.source_type}`",
        f"- Input: `{report.input_path}`",
        f"- Output: `{report.output_path}`",
        f"- Relations output: `{report.relations_output_path or 'none'}`",
        f"- Documents: {report.document_count}",
        f"- Entities mapped: {report.entity_count}",
        f"- Relations mapped: {report.relation_count}",
        "",
        "## Project Entity Label Counts",
        *([f"- {label}: {count}" for label, count in report.project_entity_label_counts.items()] or ["- none"]),
        "",
        "## Project Relation Label Counts",
        *([f"- {label}: {count}" for label, count in report.project_relation_label_counts.items()] or ["- none"]),
        "",
        "## Dropped Unmapped Entity Labels",
        *([f"- {label}: {count}" for label, count in report.dropped_entity_label_counts.items()] or ["- none"]),
        "",
        "## Dropped Unmapped/Unresolved Relations",
        *([f"- {label}: {count}" for label, count in report.dropped_relation_label_counts.items()] or ["- none"]),
        "",
        "## Warnings",
        *([f"- {w}" for w in report.warnings] if report.warnings else ["- none"]),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import a real external biomedical corpus into project gold_entities format.")
    parser.add_argument("--corpus", required=True, help="Corpus key in the crosswalk config (e.g. bc5cdr, biored).")
    parser.add_argument("--input", type=Path, required=True, help="Raw corpus file or BioC JSON directory for the reader.")
    parser.add_argument("--output", type=Path, required=True, help="Output gold_entities JSONL path.")
    parser.add_argument(
        "--relations-output",
        type=Path,
        help="Optional gold_relations JSONL path (defaults beside --output when relations are mapped).",
    )
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = import_external_corpus(
        corpus=args.corpus,
        input_path=args.input,
        output_path=args.output,
        crosswalk_path=args.crosswalk,
        relations_output_path=args.relations_output,
    )
    if args.json_output:
        save_external_corpus_import_json(report, args.json_output)
    if args.markdown_output:
        save_external_corpus_import_markdown(report, args.markdown_output)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_external_corpus_import_markdown(report))
    # Dropped unmapped labels are a warning, not a failure; only an empty mapping fails.
    return 0 if report.entity_count else 1


# ------------------------------------------------------------------------- helpers


def _join_tokens(tokens: list[str]) -> tuple[str, list[int]]:
    """Join tokens with single spaces and return the start offset of each token."""

    offsets: list[int] = []
    cursor = 0
    for index, token in enumerate(tokens):
        if index:
            cursor += 1  # the joining space
        offsets.append(cursor)
        cursor += len(token)
    return " ".join(tokens), offsets


def _spans_from_bio(tokens: list[str], tags: list[int], offsets: list[int], text: str) -> list[CorpusEntity]:
    entities: list[CorpusEntity] = []
    current_type: str | None = None
    start_idx: int | None = None
    for index, tag in enumerate(tags):
        bio_type = _BC5CDR_TAGS.get(tag)
        bio = bio_type[0] if bio_type else "O"
        etype = bio_type[1] if bio_type else None
        if bio == "B" or (bio == "I" and current_type != etype):
            if current_type is not None and start_idx is not None:
                entities.append(_make_entity(tokens, offsets, text, start_idx, index - 1, current_type))
            current_type = etype
            start_idx = index
        elif bio == "O":
            if current_type is not None and start_idx is not None:
                entities.append(_make_entity(tokens, offsets, text, start_idx, index - 1, current_type))
            current_type = None
            start_idx = None
    if current_type is not None and start_idx is not None:
        entities.append(_make_entity(tokens, offsets, text, start_idx, len(tokens) - 1, current_type))
    return entities


def _make_entity(tokens: list[str], offsets: list[int], text: str, start_idx: int, end_idx: int, etype: str) -> CorpusEntity:
    start = offsets[start_idx]
    end = offsets[end_idx] + len(tokens[end_idx])
    return CorpusEntity(text=text[start:end], label=etype, start=start, end=end)


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL record must be an object on line {line_number}: {path}")
            rows.append(payload)
    return rows


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return output


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"crosswalk JSON must be an object: {path}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
