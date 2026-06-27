"""Corpus manifest generation for reproducible GBM-AI snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared for normal installs.
    load_dotenv = None

LOGGER = logging.getLogger(__name__)
_ENV_LOADED = False


class CorpusFileManifest(BaseModel):
    """Manifest metadata for one corpus artifact."""

    model_config = ConfigDict(str_strip_whitespace=True)

    path: str
    sha256: str
    byte_count: int
    line_count: int
    non_empty_line_count: int


class CorpusManifest(BaseModel):
    """Reproducibility manifest for a corpus snapshot."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    generated_at_utc: str
    files: list[CorpusFileManifest] = Field(default_factory=list)
    query_pack: str | None = None
    source: str | None = None
    command: str | None = None
    record_count: int = 0
    environment: dict[str, bool] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


def build_corpus_manifest(
    paths: list[str | Path],
    *,
    name: str,
    query_pack: str | None = None,
    source: str | None = None,
    command: str | None = None,
    notes: list[str] | None = None,
) -> CorpusManifest:
    """Build a manifest from exact local corpus artifact paths."""

    _load_environment()
    file_manifests = [inspect_corpus_file(path) for path in paths]
    return CorpusManifest(
        name=name,
        generated_at_utc=datetime.now(UTC).replace(microsecond=0).isoformat(),
        files=file_manifests,
        query_pack=query_pack,
        source=source,
        command=command,
        record_count=sum(_record_count_for_manifest_file(item) for item in file_manifests),
        environment={
            "NCBI_EMAIL_set": bool(os.getenv("NCBI_EMAIL")),
            "NCBI_API_KEY_set": bool(os.getenv("NCBI_API_KEY")),
            "NCBI_TOOL_set": bool(os.getenv("NCBI_TOOL")),
        },
        notes=notes or [],
    )


def inspect_corpus_file(path: str | Path) -> CorpusFileManifest:
    input_path = Path(path)
    digest = hashlib.sha256()
    byte_count = 0
    line_count = 0
    non_empty_line_count = 0
    with input_path.open("rb") as handle:
        for raw_line in handle:
            digest.update(raw_line)
            byte_count += len(raw_line)
            line_count += 1
            if raw_line.strip():
                non_empty_line_count += 1
    return CorpusFileManifest(
        path=str(input_path),
        sha256=digest.hexdigest().upper(),
        byte_count=byte_count,
        line_count=line_count,
        non_empty_line_count=non_empty_line_count,
    )


def _record_count_for_manifest_file(item: CorpusFileManifest) -> int:
    suffix = Path(item.path).suffix.lower()
    if suffix == ".jsonl":
        return item.non_empty_line_count
    if suffix in {".csv", ".tsv"}:
        return max(item.non_empty_line_count - 1, 0)
    return 0


def _load_environment() -> None:
    global _ENV_LOADED
    if _ENV_LOADED or load_dotenv is None:
        return
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            load_dotenv(dotenv_path=env_path, encoding="utf-8")
        except UnicodeDecodeError:
            load_dotenv(dotenv_path=env_path, encoding="utf-16")
    _ENV_LOADED = True


def save_corpus_manifest(manifest: CorpusManifest, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    LOGGER.info("Saved corpus manifest to %s", output_path)
    return output_path


def format_corpus_manifest_markdown(manifest: CorpusManifest) -> str:
    lines = [
        f"# Corpus Manifest: {manifest.name}",
        "",
        "Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.",
        "",
        f"- Generated UTC: {manifest.generated_at_utc}",
        f"- Source: {manifest.source or 'n/a'}",
        f"- Query pack: {manifest.query_pack or 'n/a'}",
        f"- Record count: {manifest.record_count}",
        f"- Command: `{manifest.command or 'n/a'}`",
        f"- NCBI email configured: {manifest.environment.get('NCBI_EMAIL_set', False)}",
        f"- NCBI API key configured: {manifest.environment.get('NCBI_API_KEY_set', False)}",
        "",
        "## Files",
    ]
    if manifest.files:
        lines.extend(_format_manifest_file_line(item) for item in manifest.files)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Notes")
    lines.extend(f"- {note}" for note in manifest.notes) if manifest.notes else lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def _format_manifest_file_line(item: CorpusFileManifest) -> str:
    record_count = _record_count_for_manifest_file(item)
    if record_count:
        count_label = f"{record_count} records"
    else:
        count_label = f"{item.non_empty_line_count} non-empty lines"
    return f"- `{item.path}`: {count_label}, {item.byte_count} bytes, SHA256 `{item.sha256}`"


def save_corpus_manifest_markdown(manifest: CorpusManifest, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_corpus_manifest_markdown(manifest), encoding="utf-8")
    LOGGER.info("Saved corpus manifest Markdown to %s", output_path)
    return output_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a reproducibility manifest for corpus JSONL files.")
    parser.add_argument("paths", nargs="+", type=Path, help="Corpus artifact path(s).")
    parser.add_argument("--name", required=True)
    parser.add_argument("--query-pack")
    parser.add_argument("--source")
    parser.add_argument("--command")
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True, help="Output JSON manifest path.")
    parser.add_argument("--markdown-output", type=Path, help="Optional Markdown manifest path.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    manifest = build_corpus_manifest(
        args.paths,
        name=args.name,
        query_pack=args.query_pack,
        source=args.source,
        command=args.command,
        notes=args.note,
    )
    save_corpus_manifest(manifest, args.output)
    if args.markdown_output:
        save_corpus_manifest_markdown(manifest, args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
