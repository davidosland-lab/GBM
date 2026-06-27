"""Curated PubMed query packs for GBM-AI literature backfills."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from gbmbert.ingest.pubmed import fetch_pubmed_records, save_jsonl, search_pubmed

LOGGER = logging.getLogger(__name__)
DEFAULT_QUERY_PACK_DIR = Path("data/query_packs")
DEFAULT_OUTPUT_DIR = Path("data/raw")


class PubMedQueryPack(BaseModel):
    """A named group of PubMed searches with source provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    description: str = ""
    source: str = ""
    queries: list[str] = Field(default_factory=list)

    @field_validator("queries")
    @classmethod
    def queries_must_not_be_empty(cls, value: list[str]) -> list[str]:
        queries = [query.strip() for query in value if query.strip()]
        if not queries:
            raise ValueError("query pack must contain at least one query")
        return queries


def query_pack_path(name: str, pack_dir: str | Path = DEFAULT_QUERY_PACK_DIR) -> Path:
    """Return the JSON path for a query pack name or direct path."""

    candidate = Path(name)
    if candidate.suffix == ".json" or candidate.exists():
        return candidate
    return Path(pack_dir) / f"{name}.json"


def list_query_packs(pack_dir: str | Path = DEFAULT_QUERY_PACK_DIR) -> list[str]:
    """List available query pack names."""

    path = Path(pack_dir)
    if not path.exists():
        return []
    return sorted(item.stem for item in path.glob("*.json"))


def load_query_pack(name: str, pack_dir: str | Path = DEFAULT_QUERY_PACK_DIR) -> PubMedQueryPack:
    """Load and validate a PubMed query pack JSON file."""

    path = query_pack_path(name, pack_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        available = ", ".join(list_query_packs(pack_dir)) or "none"
        raise ValueError(f"Unknown query pack {name!r}; available packs: {available}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid query pack JSON: {path}") from exc
    return PubMedQueryPack.model_validate(payload)


def search_query_pack(
    pack: PubMedQueryPack,
    *,
    retmax_per_query: int = 25,
    sort: str = "relevance",
    search_fn: Callable[..., list[str]] = search_pubmed,
) -> dict[str, list[str]]:
    """Run all searches in a query pack and return PMIDs grouped by query."""

    if retmax_per_query < 1:
        raise ValueError("retmax_per_query must be at least 1")
    results: dict[str, list[str]] = {}
    for query in pack.queries:
        LOGGER.info("Searching PubMed query pack %s: %s", pack.name, query)
        results[query] = search_fn(query, retmax=retmax_per_query, sort=sort)
    return results


def unique_pmids(search_results: dict[str, Sequence[str]]) -> list[str]:
    """Return stable unique PMIDs from grouped query results."""

    seen: set[str] = set()
    pmids: list[str] = []
    for query_pmids in search_results.values():
        for pmid in query_pmids:
            normalized = str(pmid).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                pmids.append(normalized)
    return pmids


def annotate_records_with_query_pack(
    records: Iterable[dict[str, Any]],
    *,
    pack: PubMedQueryPack,
    search_results: dict[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Attach query-pack provenance to fetched PubMed records."""

    queries_by_pmid: dict[str, list[str]] = {}
    for query, pmids in search_results.items():
        for pmid in pmids:
            queries_by_pmid.setdefault(str(pmid), []).append(query)

    annotated = []
    for record in records:
        pmid = str(record.get("pmid", ""))
        annotated.append(
            {
                **record,
                "query_pack": pack.name,
                "query_pack_source": pack.source,
                "matched_queries": sorted(set(queries_by_pmid.get(pmid, []))),
            }
        )
    return annotated


def run_query_pack(
    pack_name: str,
    *,
    pack_dir: str | Path = DEFAULT_QUERY_PACK_DIR,
    output: str | Path | None = None,
    retmax_per_query: int = 25,
    sort: str = "relevance",
) -> Path:
    """Search, fetch, annotate, and save PubMed records for a query pack."""

    pack = load_query_pack(pack_name, pack_dir)
    search_results = search_query_pack(pack, retmax_per_query=retmax_per_query, sort=sort)
    pmids = unique_pmids(search_results)
    records = fetch_pubmed_records(pmids)
    annotated = annotate_records_with_query_pack(records, pack=pack, search_results=search_results)
    output_path = Path(output) if output else DEFAULT_OUTPUT_DIR / f"{pack.name}.jsonl"
    return save_jsonl(annotated, output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search PubMed using a curated GBM-AI query pack.")
    parser.add_argument("--query-pack", help="Query pack name or JSON path.")
    parser.add_argument("--pack-dir", type=Path, default=DEFAULT_QUERY_PACK_DIR)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--retmax-per-query", type=int, default=25)
    parser.add_argument("--sort", default="relevance")
    parser.add_argument("--list-packs", action="store_true", help="List available query packs and exit.")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    if args.list_packs:
        for name in list_query_packs(args.pack_dir):
            print(name)
        return 0
    if not args.query_pack:
        parser.error("--query-pack is required unless --list-packs is used")
    output_path = run_query_pack(
        args.query_pack,
        pack_dir=args.pack_dir,
        output=args.output,
        retmax_per_query=args.retmax_per_query,
        sort=args.sort,
    )
    LOGGER.info("Saved query-pack PubMed records to %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
