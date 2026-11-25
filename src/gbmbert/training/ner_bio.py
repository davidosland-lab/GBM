"""Build document-level BIO NER packs from gold_entities + PubMed abstracts."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from gbmbert.datasets import RESEARCH_WARNING

DEFAULT_ENTITY_GLOBS = (
    "data/training/curated_expansion/gold_entities*.jsonl",
    "data/training/gold_seed/gold_entities.jsonl",
    # GBM-filtered EBM-NLP Intervention/Outcome docs (embedded text + offsets).
    "data/training/external_corpus/ebm_nlp_gbm/gold_entities.jsonl",
)
DEFAULT_PUBMED_SOURCES = (
    "data/raw/pubmed_gbm_merged_backfill_2026-07-18.jsonl",
    "data/research/review_batches/round*/pubmed_round*_candidates.jsonl",
)
DEFAULT_OUTPUT_DIR = Path("data/training/ner_bio_pack")

# Sparse types that must appear in train+test when enough PMIDs exist.
SPARSE_ENTITY_TYPES = ("CELL_STATE", "PATHWAY", "TRIAL_PHASE")

# Keyword-dump UNKNOWN mentions are not span-quality entities; drop by default.
UNKNOWN_NOISE_TEXTS = frozenset(
    {
        "unclear",
        "elusive",
        "putative",
        "equivocal",
        "furthermore",
        "however",
        "context",
        "indeterminate",
        "respectively",
        "uncharacterized",
        "therefore",
        "nos",
        "poorly characterized",
        "poorly understood",
        "non-specific",
        "nonspecific",
        "undetermined",
        "circuit",
        "unknown",
        "uncertain",
    }
)

# Single-token gene symbols wrongly labeled PATHWAY in keyword densify rounds.
PATHWAY_GENE_SYMBOLS = frozenset(
    {
        "egfr",
        "akt",
        "pi3k",
        "pd-l1",
        "pdl1",
        "met",
        "ras",
        "braf",
        "tp53",
        "pten",
        "mgmt",
        "vegf",
        "myc",
        "mdm2",
        "tert",
        "atrx",
        "nf1",
        "cdk4",
        "cdk6",
        "pik3ca",
        "pdgfra",
        "idh1",
        "idh2",
    }
)


@dataclass(frozen=True)
class NerBioPackReport:
    output_dir: str
    document_count: int
    entity_count: int
    split_counts: dict[str, int]
    entity_type_counts: dict[str, int]
    label_map_path: str
    files: dict[str, str]
    warnings: list[str]
    warning: str = RESEARCH_WARNING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_ner_bio_pack(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    entity_jsonl: list[str | Path] | None = None,
    pubmed_jsonl: list[str | Path] | None = None,
    seed: int = 13,
    train_ratio: float = 0.8,
    validation_ratio: float = 0.1,
    drop_unknown_noise: bool = True,
    drop_all_unknown: bool = True,
    remap_pathway_gene_symbols: bool = True,
    stratified_sparse_types: bool = True,
    oversample_sparse_train: int = 2,
) -> NerBioPackReport:
    """Join char-offset gold entities to PubMed text and emit PMID-split BIO docs."""

    output_root = Path(output_dir)
    split_dir = output_root / "annotation_splits"
    label_dir = output_root / "label_maps"
    split_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    entity_paths = _resolve_paths(entity_jsonl, DEFAULT_ENTITY_GLOBS)
    pubmed_paths = _resolve_paths(pubmed_jsonl, DEFAULT_PUBMED_SOURCES)
    abstracts = _load_pubmed_texts(pubmed_paths)
    docs_by_pmid = _load_entity_docs(entity_paths)

    rows: list[dict[str, Any]] = []
    skipped_missing_text = 0
    skipped_bad_span = 0
    dropped_unknown_noise = 0
    remapped_pathway_genes = 0
    entity_type_counts: Counter[str] = Counter()
    for pmid, payload in sorted(docs_by_pmid.items()):
        entities = payload["entities"]
        # Prefer embedded corpus text (EBM-NLP offsets) over PubMed title+abstract join.
        text = str(payload.get("text") or "").strip() or abstracts.get(pmid)
        if not text:
            skipped_missing_text += 1
            continue
        kept: list[dict[str, Any]] = []
        for entity in entities:
            start = int(entity.get("start", -1))
            end = int(entity.get("end", -1))
            label = str(entity.get("label") or "").strip()
            mention = str(entity.get("text") or "")
            if not label or start < 0 or end <= start or end > len(text):
                skipped_bad_span += 1
                continue
            if text[start:end] != mention and mention:
                # Prefer exact offsets; fall back only when the mention still occurs.
                found = text.find(mention)
                if found < 0:
                    skipped_bad_span += 1
                    continue
                start, end = found, found + len(mention)
            mention_text = mention or text[start:end]
            if label == "UNKNOWN":
                if drop_all_unknown or (drop_unknown_noise and _is_unknown_noise(mention_text)):
                    dropped_unknown_noise += 1
                    continue
            if label == "PATHWAY" and remap_pathway_gene_symbols and _is_pathway_gene_symbol(mention_text):
                label = "GENE"
                remapped_pathway_genes += 1
            kept.append(
                {
                    "text": mention_text,
                    "label": label,
                    "start": start,
                    "end": end,
                    "normalized_text": str(entity.get("normalized_text") or mention_text),
                    "confidence": entity.get("confidence"),
                }
            )
            entity_type_counts[label] += 1
        if not kept:
            continue
        rows.append(
            {
                "task": "ner",
                "ner_encoding": "bio",
                "source_pmid": pmid,
                "text": text,
                "label": kept[0]["label"],
                "entities": kept,
                "warning": RESEARCH_WARNING,
            }
        )

    if skipped_missing_text:
        warnings.append(f"skipped {skipped_missing_text} entity doc(s) with no matching PubMed text")
    if skipped_bad_span:
        warnings.append(f"skipped {skipped_bad_span} entity span(s) with invalid/unaligned offsets")
    if dropped_unknown_noise:
        mode = "all UNKNOWN" if drop_all_unknown else "noisy UNKNOWN"
        warnings.append(f"dropped {dropped_unknown_noise} {mode} span(s) (keyword-dump cleanup)")
    if remapped_pathway_genes:
        warnings.append(f"remapped {remapped_pathway_genes} gene-symbol PATHWAY span(s) to GENE")

    if stratified_sparse_types:
        splits = _pmid_split_stratified_sparse(
            rows,
            seed=seed,
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            sparse_types=SPARSE_ENTITY_TYPES,
        )
        warnings.append("used stratified PMID split preserving sparse entity types in train+test")
    else:
        splits = _pmid_split(rows, seed=seed, train_ratio=train_ratio, validation_ratio=validation_ratio)

    if oversample_sparse_train > 1:
        before = len(splits["train"])
        splits["train"] = _oversample_sparse_docs(
            splits["train"],
            sparse_types=SPARSE_ENTITY_TYPES,
            copies=oversample_sparse_train,
        )
        warnings.append(
            f"oversampled sparse-type train docs x{oversample_sparse_train} ({before} -> {len(splits['train'])})"
        )
    files: dict[str, str] = {}
    for split_name, split_rows in splits.items():
        path = split_dir / f"ner_{split_name}.jsonl"
        _write_jsonl(split_rows, path)
        files[split_name] = str(path)

    entity_types = sorted(entity_type_counts)
    bio_labels = ["O"] + [f"B-{label}" for label in entity_types] + [f"I-{label}" for label in entity_types]
    label_to_id = {label: index for index, label in enumerate(bio_labels)}
    label_map_path = label_dir / "ner_label_map.json"
    label_map_path.write_text(
        json.dumps(
            {
                "task": "ner",
                "encoding": "bio",
                "entity_types": entity_types,
                "label_to_id": label_to_id,
                "id_to_label": {str(index): label for label, index in label_to_id.items()},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    files["label_map"] = str(label_map_path)

    report = NerBioPackReport(
        output_dir=str(output_root),
        document_count=len(rows),
        entity_count=sum(entity_type_counts.values()),
        split_counts={name: len(values) for name, values in splits.items()},
        entity_type_counts=dict(sorted(entity_type_counts.items())),
        label_map_path=str(label_map_path),
        files=files,
        warnings=warnings,
    )
    (output_root / "ner_bio_pack_report.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_root / "ner_bio_pack_report.md").write_text(format_ner_bio_pack_markdown(report), encoding="utf-8")
    return report


def format_ner_bio_pack_markdown(report: NerBioPackReport) -> str:
    warnings = [f"- {item}" for item in report.warnings] if report.warnings else ["- none"]
    types = [f"- {label}: {count}" for label, count in report.entity_type_counts.items()]
    return "\n".join(
        [
            "# NER BIO Pack Report",
            "",
            report.warning,
            "",
            f"- Output dir: `{report.output_dir}`",
            f"- Documents: {report.document_count}",
            f"- Entity spans: {report.entity_count}",
            f"- Splits: {report.split_counts}",
            f"- Label map: `{report.label_map_path}`",
            "",
            "## Entity types",
            *(types or ["- none"]),
            "",
            "## Warnings",
            *warnings,
            "",
        ]
    )


def bio_label_map_is_bio(label_to_id: dict[str, int]) -> bool:
    labels = set(label_to_id)
    return "O" in labels and any(label.startswith("B-") for label in labels)


def align_bio_labels(
    *,
    text: str,
    entities: list[dict[str, Any]],
    offset_mapping: list[tuple[int, int]],
    label_to_id: dict[str, int],
) -> list[int]:
    """Map char-span entities onto tokenizer offsets as BIO ids (-100 for specials)."""

    o_id = label_to_id["O"]
    labels = [-100 if start == end == 0 else o_id for start, end in offset_mapping]
    ordered = sorted(
        entities,
        key=lambda item: (int(item.get("start", 0)), -(int(item.get("end", 0)) - int(item.get("start", 0)))),
    )
    for entity in ordered:
        start = int(entity.get("start", -1))
        end = int(entity.get("end", -1))
        entity_type = str(entity.get("label") or "").strip()
        if start < 0 or end <= start or end > len(text) or not entity_type:
            continue
        b_key = f"B-{entity_type}"
        i_key = f"I-{entity_type}"
        if b_key not in label_to_id or i_key not in label_to_id:
            continue
        first = True
        for index, (tok_start, tok_end) in enumerate(offset_mapping):
            if tok_start == tok_end == 0:
                continue
            if tok_end <= start or tok_start >= end:
                continue
            labels[index] = label_to_id[b_key] if first else label_to_id[i_key]
            first = False
    return labels


def spans_from_bio_ids(label_ids: list[int], id_to_label: dict[int, str]) -> list[tuple[int, int, str]]:
    """Convert token BIO ids into inclusive token-index spans (start, end, type)."""

    spans: list[tuple[int, int, str]] = []
    index = 0
    while index < len(label_ids):
        label_id = int(label_ids[index])
        if label_id < 0:
            index += 1
            continue
        tag = id_to_label.get(label_id, "O")
        if not tag.startswith("B-"):
            index += 1
            continue
        entity_type = tag[2:]
        end = index
        cursor = index + 1
        while cursor < len(label_ids):
            next_id = int(label_ids[cursor])
            if next_id < 0:
                break
            next_tag = id_to_label.get(next_id, "O")
            if next_tag == f"I-{entity_type}":
                end = cursor
                cursor += 1
                continue
            break
        spans.append((index, end, entity_type))
        index = cursor
    return spans


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a document-level BIO NER pack from gold entities.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--entity-jsonl", type=Path, action="append", default=None)
    parser.add_argument("--pubmed-jsonl", type=Path, action="append", default=None)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = build_ner_bio_pack(
        output_dir=args.output_dir,
        entity_jsonl=args.entity_jsonl,
        pubmed_jsonl=args.pubmed_jsonl,
        seed=args.seed,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else format_ner_bio_pack_markdown(report))
    return 0


def _resolve_paths(explicit: list[str | Path] | None, globs: tuple[str, ...]) -> list[Path]:
    if explicit:
        return [Path(path) for path in explicit]
    found: list[Path] = []
    root = Path(".")
    for pattern in globs:
        found.extend(sorted(root.glob(pattern)))
    return found


def _load_pubmed_texts(paths: list[Path]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            pmid = str(row.get("pmid") or "").strip()
            if not pmid:
                continue
            title = str(row.get("title") or "").strip()
            abstract = str(row.get("abstract") or "").strip()
            text = f"{title} {abstract}".strip()
            if len(text) >= 20:
                texts[pmid] = text
    return texts


def _load_entity_docs(paths: list[Path]) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            pmid = str(row.get("pmid") or row.get("source_pmid") or "").strip()
            entities = row.get("entities")
            if not pmid or not isinstance(entities, list):
                continue
            # Later files win for the same PMID (newer curated rounds / external folds).
            docs[pmid] = {
                "entities": [entity for entity in entities if isinstance(entity, dict)],
                "text": str(row.get("text") or "").strip(),
            }
    return docs


def _pmid_split(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> dict[str, list[dict[str, Any]]]:
    pmids = sorted({str(row["source_pmid"]) for row in rows})
    rng = random.Random(seed)
    rng.shuffle(pmids)
    n_train = int(len(pmids) * train_ratio)
    n_val = int(len(pmids) * validation_ratio)
    train_pmids = set(pmids[:n_train])
    val_pmids = set(pmids[n_train : n_train + n_val])
    test_pmids = set(pmids[n_train + n_val :])
    # Keep non-empty splits on tiny packs.
    if not val_pmids and pmids:
        val_pmids = {pmids[-1]}
        train_pmids.discard(pmids[-1])
    if not test_pmids and pmids:
        candidate = next((pmid for pmid in reversed(pmids) if pmid not in val_pmids), pmids[0])
        test_pmids = {candidate}
        train_pmids.discard(candidate)
    return _bucket_rows_by_pmid(rows, train_pmids=train_pmids, val_pmids=val_pmids, test_pmids=test_pmids)


def _pmid_split_stratified_sparse(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
    sparse_types: tuple[str, ...],
) -> dict[str, list[dict[str, Any]]]:
    """PMID split that reserves sparse-type docs for train and test (and val when possible)."""

    rng = random.Random(seed)
    by_pmid = {str(row["source_pmid"]): row for row in rows}
    remaining = set(by_pmid)
    train_pmids: set[str] = set()
    val_pmids: set[str] = set()
    test_pmids: set[str] = set()

    for entity_type in sparse_types:
        carriers = sorted(
            pmid
            for pmid in remaining
            if any(str(entity.get("label") or "") == entity_type for entity in by_pmid[pmid].get("entities") or [])
        )
        rng.shuffle(carriers)
        if not carriers:
            continue
        # Prefer at least one train + one test carrier when >=2 PMIDs; add val when >=3.
        if len(carriers) >= 3:
            train_pmids.add(carriers[0])
            test_pmids.add(carriers[1])
            val_pmids.add(carriers[2])
            for pmid in carriers[3:]:
                train_pmids.add(pmid)
        elif len(carriers) == 2:
            train_pmids.add(carriers[0])
            test_pmids.add(carriers[1])
        else:
            # Single carrier: keep in train so the model sees the type.
            train_pmids.add(carriers[0])
        remaining -= set(carriers)

    leftover = sorted(remaining)
    rng.shuffle(leftover)
    n_train = int(len(by_pmid) * train_ratio)
    n_val = int(len(by_pmid) * validation_ratio)
    for pmid in leftover:
        if len(train_pmids) < n_train:
            train_pmids.add(pmid)
        elif len(val_pmids) < n_val:
            val_pmids.add(pmid)
        else:
            test_pmids.add(pmid)

    # Ensure non-empty splits.
    all_pmids = sorted(by_pmid)
    if not val_pmids and all_pmids:
        donor = next((pmid for pmid in reversed(all_pmids) if pmid in train_pmids), all_pmids[-1])
        val_pmids.add(donor)
        train_pmids.discard(donor)
    if not test_pmids and all_pmids:
        donor = next(
            (pmid for pmid in reversed(all_pmids) if pmid in train_pmids and pmid not in val_pmids),
            all_pmids[0],
        )
        test_pmids.add(donor)
        train_pmids.discard(donor)

    return _bucket_rows_by_pmid(rows, train_pmids=train_pmids, val_pmids=val_pmids, test_pmids=test_pmids)


def _bucket_rows_by_pmid(
    rows: list[dict[str, Any]],
    *,
    train_pmids: set[str],
    val_pmids: set[str],
    test_pmids: set[str],
) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for row in rows:
        pmid = str(row["source_pmid"])
        if pmid in train_pmids:
            buckets["train"].append(row)
        elif pmid in val_pmids:
            buckets["validation"].append(row)
        else:
            buckets["test"].append(row)
    return buckets


def _oversample_sparse_docs(
    rows: list[dict[str, Any]],
    *,
    sparse_types: tuple[str, ...],
    copies: int,
) -> list[dict[str, Any]]:
    if copies <= 1:
        return list(rows)
    sparse_set = set(sparse_types)
    extra: list[dict[str, Any]] = []
    for row in rows:
        labels = {str(entity.get("label") or "") for entity in row.get("entities") or []}
        if labels & sparse_set:
            extra.extend([row] * (copies - 1))
    return list(rows) + extra


def _is_unknown_noise(text: str) -> bool:
    normalized = " ".join(text.strip().casefold().split())
    return normalized in UNKNOWN_NOISE_TEXTS


def _is_pathway_gene_symbol(text: str) -> bool:
    normalized = text.strip().casefold()
    return normalized in PATHWAY_GENE_SYMBOLS and "/" not in normalized and " " not in normalized


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
