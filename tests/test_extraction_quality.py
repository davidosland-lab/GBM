import json
from pathlib import Path

from gbmbert.annotation.schema import EntityType
from gbmbert.extraction.entities import EntityExtractionResult, ExtractedEntity
from gbmbert.extraction.io import save_entity_jsonl
from gbmbert.extraction.quality import (
    build_entity_quality_report,
    format_entity_quality_markdown,
    main,
)


def test_build_entity_quality_report_counts_entities_and_offsets(tmp_path: Path) -> None:
    pubmed_path, entity_path = _write_quality_inputs(tmp_path)

    report = build_entity_quality_report(
        entity_path,
        pubmed_jsonl=pubmed_path,
        low_confidence_threshold=0.5,
    )

    assert report.paper_count == 2
    assert report.source_paper_count == 2
    assert report.entity_count == 4
    assert report.empty_paper_count == 1
    assert report.unknown_entity_count == 1
    assert report.unknown_entity_rate == 0.25
    assert report.average_entities_per_paper == 2.0
    assert report.low_confidence_count == 1
    assert report.invalid_offset_count == 1
    assert report.text_mismatch_count == 0
    assert report.missing_source_pmid_count == 0
    assert [(item.key, item.count) for item in report.label_counts] == [
        ("DISEASE", 1),
        ("GENE", 1),
        ("UNKNOWN", 1),
        ("DRUG", 1),
    ]
    assert report.offset_issues[0].reason == "invalid span"
    assert "UNKNOWN entity rate is at least 25%" in report.warnings


def test_format_entity_quality_markdown_includes_summary_sections(tmp_path: Path) -> None:
    pubmed_path, entity_path = _write_quality_inputs(tmp_path)
    report = build_entity_quality_report(entity_path, pubmed_jsonl=pubmed_path)

    markdown = format_entity_quality_markdown(report)

    assert "Entity Extraction Quality Report" in markdown
    assert "- Entities: 4" in markdown
    assert "## Labels" in markdown
    assert "- DISEASE: 1" in markdown
    assert "## Offset Issue Samples" in markdown


def test_entity_quality_cli_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    pubmed_path, entity_path = _write_quality_inputs(tmp_path)
    json_output = tmp_path / "quality.json"
    markdown_output = tmp_path / "quality.md"

    exit_code = main(
        [
            str(entity_path),
            "--pubmed-jsonl",
            str(pubmed_path),
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
            "--json",
        ]
    )

    assert exit_code == 0
    assert json.loads(json_output.read_text(encoding="utf-8"))["entity_count"] == 4
    assert "Entity Extraction Quality Report" in markdown_output.read_text(encoding="utf-8")
    assert json.loads(capsys.readouterr().out)["invalid_offset_count"] == 1


def test_entity_quality_report_warns_when_source_text_is_missing(tmp_path: Path) -> None:
    _pubmed_path, entity_path = _write_quality_inputs(tmp_path)

    report = build_entity_quality_report(entity_path)

    assert report.source_paper_count is None
    assert report.invalid_offset_count == 0
    assert "PubMed source JSONL not provided; offset text validation skipped" in report.warnings


def _write_quality_inputs(tmp_path: Path) -> tuple[Path, Path]:
    pubmed_path = tmp_path / "pubmed.jsonl"
    entity_path = tmp_path / "entities.jsonl"
    pubmed_rows = [
        {
            "pmid": "12345678",
            "title": "Glioblastoma MGMT",
            "abstract": "TMZ response.",
            "journal": "Research Journal",
            "publication_date": "2026",
            "mesh_terms": ["Glioblastoma"],
        },
        {
            "pmid": "87654321",
            "title": "No entities here",
            "abstract": "",
            "journal": "Research Journal",
            "publication_date": "2026",
            "mesh_terms": [],
        },
    ]
    pubmed_path.write_text(
        "".join(json.dumps(row) + "\n" for row in pubmed_rows),
        encoding="utf-8",
    )
    results = [
        EntityExtractionResult(
            pmid="12345678",
            entities=[
                ExtractedEntity(
                    text="Glioblastoma",
                    label=EntityType.DISEASE,
                    start=0,
                    end=12,
                    confidence=0.9,
                    normalized_text="glioblastoma",
                ),
                ExtractedEntity(
                    text="MGMT",
                    label=EntityType.GENE,
                    start=13,
                    end=17,
                    confidence=0.95,
                    normalized_text="MGMT",
                ),
                ExtractedEntity(
                    text="TMZ",
                    label=EntityType.UNKNOWN,
                    start=18,
                    end=21,
                    confidence=0.4,
                    normalized_text="temozolomide",
                ),
                ExtractedEntity(
                    text="bad",
                    label=EntityType.DRUG,
                    start=100,
                    end=103,
                    confidence=0.7,
                    normalized_text="bad",
                ),
            ],
        ),
        EntityExtractionResult(pmid="87654321", entities=[]),
    ]
    save_entity_jsonl(results, entity_path)
    return pubmed_path, entity_path
