import json
from pathlib import Path

from gbmbert.ingest.manifest import (
    build_corpus_manifest,
    format_corpus_manifest_markdown,
    save_corpus_manifest,
    save_corpus_manifest_markdown,
)


def test_build_corpus_manifest_hashes_files_and_counts_records(
    tmp_path: Path,
    monkeypatch,
) -> None:
    corpus_path = tmp_path / "pubmed.jsonl"
    corpus_path.write_text('{"pmid":"1"}\n{"pmid":"2"}\n\n', encoding="utf-8")
    monkeypatch.setenv("NCBI_EMAIL", "research@example.org")
    monkeypatch.setenv("NCBI_API_KEY", "secret")

    manifest = build_corpus_manifest(
        [corpus_path],
        name="test corpus",
        query_pack="pubmed_gbm_v1",
        source="PubMed",
        command="gbmbert-search-pubmed ...",
        notes=["small smoke fixture"],
    )

    assert manifest.name == "test corpus"
    assert manifest.record_count == 2
    assert manifest.files[0].line_count == 3
    assert manifest.files[0].non_empty_line_count == 2
    assert len(manifest.files[0].sha256) == 64
    assert manifest.environment["NCBI_EMAIL_set"] is True
    assert manifest.environment["NCBI_API_KEY_set"] is True
    assert manifest.notes == ["small smoke fixture"]


def test_save_corpus_manifest_json_and_markdown(tmp_path: Path) -> None:
    corpus_path = tmp_path / "pubmed.jsonl"
    corpus_path.write_text('{"pmid":"1"}\n', encoding="utf-8")
    manifest = build_corpus_manifest([corpus_path], name="test corpus")
    json_path = tmp_path / "manifest.json"
    markdown_path = tmp_path / "manifest.md"

    save_corpus_manifest(manifest, json_path)
    save_corpus_manifest_markdown(manifest, markdown_path)
    markdown = format_corpus_manifest_markdown(manifest)

    assert json.loads(json_path.read_text(encoding="utf-8"))["record_count"] == 1
    assert "# Corpus Manifest: test corpus" in markdown_path.read_text(encoding="utf-8")
    assert "Research-use only. Not medical advice." in markdown


def test_corpus_manifest_counts_only_record_bearing_files(tmp_path: Path) -> None:
    corpus_path = tmp_path / "pubmed.jsonl"
    report_path = tmp_path / "quality.md"
    corpus_path.write_text('{"pmid":"1"}\n{"pmid":"2"}\n', encoding="utf-8")
    report_path.write_text("# Quality\n\n- Valid records: 2\n", encoding="utf-8")

    manifest = build_corpus_manifest([corpus_path, report_path], name="mixed artifacts")
    markdown = format_corpus_manifest_markdown(manifest)

    assert manifest.record_count == 2
    assert "pubmed.jsonl`: 2 records" in markdown
    assert "quality.md`: 2 non-empty lines" in markdown
