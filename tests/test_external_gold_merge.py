import json
from pathlib import Path

from gbmbert.training.external_corpus_import import EXTERNAL_SOURCE_TYPE
from gbmbert.training.external_gold_merge import (
    HUMAN_REVIEWED_SOURCE_TYPE,
    document_is_gbm_adjacent,
    filter_external_entities,
    load_gbm_relevance_patterns,
    merge_external_gold_pack,
    write_gbm_filtered_external_entities,
)
from gbmbert.training.governance import audit_training_provenance


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_gbm_relevance_patterns_match_glioblastoma_and_u87() -> None:
    patterns = load_gbm_relevance_patterns(Path("configs/extraction/gbm_relevance_keywords.json"))
    ok, matched = document_is_gbm_adjacent("U87MG is a glioblastoma cell line.", patterns)
    assert ok
    assert any("glioblastoma" in m.lower() or "u87" in m.lower() for m in matched)
    ok_neg, _ = document_is_gbm_adjacent("Congenital hypothyroidism due to NIS deletion.", patterns)
    assert not ok_neg


def test_filter_external_entities_keeps_only_gbm_adjacent(tmp_path: Path) -> None:
    patterns = load_gbm_relevance_patterns(Path("configs/extraction/gbm_relevance_keywords.json"))
    rows = [
        {"pmid": "1", "text": "Glioblastoma therapy with temozolomide.", "entities": [], "source_type": EXTERNAL_SOURCE_TYPE},
        {"pmid": "2", "text": "Thyroid iodide transport defect.", "entities": [], "source_type": EXTERNAL_SOURCE_TYPE},
    ]
    kept, matched, dropped = filter_external_entities(rows, patterns=patterns)
    assert len(kept) == 1 and kept[0]["pmid"] == "1"
    assert dropped == 1
    assert matched


def test_merge_preserves_dual_provenance(tmp_path: Path) -> None:
    keywords = tmp_path / "keywords.json"
    keywords.write_text(json.dumps({"patterns": ["glioblastoma", r"\bGBM\b"]}), encoding="utf-8")

    external_entities = _write_jsonl(
        tmp_path / "ext_entities.jsonl",
        [
            {
                "pmid": "100",
                "text": "Glioblastoma MGMT study.",
                "source_type": EXTERNAL_SOURCE_TYPE,
                "source_corpus": "biored",
                "entities": [
                    {
                        "confidence": 1.0,
                        "end": 12,
                        "label": "DISEASE",
                        "normalized_text": "Glioblastoma",
                        "start": 0,
                        "text": "Glioblastoma",
                    }
                ],
            },
            {
                "pmid": "200",
                "text": "Unrelated thyroid disease abstract.",
                "source_type": EXTERNAL_SOURCE_TYPE,
                "source_corpus": "biored",
                "entities": [],
            },
        ],
    )
    external_relations = _write_jsonl(
        tmp_path / "ext_relations.jsonl",
        [
            {
                "source_pmid": "100",
                "label": "ASSOCIATED_WITH",
                "head": "DISEASE:Glioblastoma",
                "tail": "GENE:MGMT",
                "source_type": EXTERNAL_SOURCE_TYPE,
                "source_corpus": "biored",
                "task": "relation",
                "text": "Glioblastoma MGMT study.",
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
            },
            {
                "source_pmid": "200",
                "label": "ASSOCIATED_WITH",
                "head": "DISEASE:thyroid",
                "tail": "GENE:NIS",
                "source_type": EXTERNAL_SOURCE_TYPE,
                "source_corpus": "biored",
                "task": "relation",
                "text": "Unrelated thyroid disease abstract.",
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
            },
        ],
    )
    curated_entities = _write_jsonl(
        tmp_path / "curated_entities.jsonl",
        [
            {
                "pmid": "23209033",
                "entities": [
                    {
                        "confidence": 1.0,
                        "end": 4,
                        "label": "GENE",
                        "normalized_text": "IDH1",
                        "start": 0,
                        "text": "IDH1",
                    }
                ],
            }
        ],
    )
    curated_relations = _write_jsonl(
        tmp_path / "curated_relations.jsonl",
        [
            {
                "task": "relation",
                "source_pmid": "23209033",
                "label": "ASSOCIATED_WITH",
                "head": "Gene:IDH1",
                "tail": "Disease:glioblastoma",
                "text": "IDH1 associated with glioblastoma.",
                "relation_pack_source_type": "human_or_curated_positive",
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
            }
        ],
    )
    curated_evidence = _write_jsonl(
        tmp_path / "curated_evidence.jsonl",
        [
            {
                "task": "evidence",
                "source_pmid": "23209033",
                "label": 0,
                "text": "Review-tier glioblastoma claim.",
                "review_status": "accepted",
                "reviewer": "curator",
                "warning": "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
            }
        ],
    )

    report = merge_external_gold_pack(
        output_dir=tmp_path / "combined",
        external_entities_jsonl=external_entities,
        external_relations_jsonl=external_relations,
        curated_entities_jsonl=[curated_entities],
        curated_relations_jsonl=[curated_relations],
        curated_evidence_jsonl=[curated_evidence],
        keywords_path=keywords,
    )

    assert report.external_documents_total == 2
    assert report.external_documents_kept == 1
    assert report.external_documents_dropped == 1
    assert report.entity_document_count == 2
    assert report.relation_count == 2
    assert report.evidence_count == 1
    assert report.ner_count == 2

    entities = [json.loads(line) for line in Path(report.files["entities"]).read_text(encoding="utf-8").splitlines()]
    assert {row["source_type"] for row in entities} == {HUMAN_REVIEWED_SOURCE_TYPE, EXTERNAL_SOURCE_TYPE}

    ner = [json.loads(line) for line in Path(report.files["ner"]).read_text(encoding="utf-8").splitlines()]
    assert all("source_type" in row for row in ner)

    relations = [json.loads(line) for line in Path(report.files["relations"]).read_text(encoding="utf-8").splitlines()]
    assert {row["source_pmid"] for row in relations} == {"100", "23209033"}
    external_rel = next(row for row in relations if row["source_pmid"] == "100")
    assert external_rel["source_type"] == EXTERNAL_SOURCE_TYPE
    assert external_rel["relation_pack_source_type"] == EXTERNAL_SOURCE_TYPE

    provenance = audit_training_provenance(report.files["relations"])
    assert provenance.safe is True
    assert "external_corpus" in provenance.source_type_counts
    assert "human_or_curated_positive" in provenance.source_type_counts


def test_write_gbm_filtered_external_entities(tmp_path: Path) -> None:
    keywords = tmp_path / "keywords.json"
    keywords.write_text(json.dumps({"patterns": [r"glioblastoma", r"\bTMZ\b"]}), encoding="utf-8")
    external = _write_jsonl(
        tmp_path / "external.jsonl",
        [
            {
                "pmid": "1",
                "source_corpus": "ebm_nlp",
                "text": "Radiotherapy for glioblastoma survival",
                "entities": [{"text": "Radiotherapy", "label": "TREATMENT", "start": 0, "end": 12}],
            },
            {
                "pmid": "2",
                "source_corpus": "ebm_nlp",
                "text": "Knee replacement outcomes in osteoarthritis",
                "entities": [{"text": "Knee replacement", "label": "TREATMENT", "start": 0, "end": 16}],
            },
        ],
    )
    out = tmp_path / "ebm_nlp_gbm" / "gold_entities.jsonl"

    path, kept, dropped = write_gbm_filtered_external_entities(
        external_entities_jsonl=external,
        output_path=out,
        keywords_path=keywords,
    )

    assert path == out
    assert kept == 1
    assert dropped == 1
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["pmid"] == "1"
    assert rows[0]["source_type"] == EXTERNAL_SOURCE_TYPE
