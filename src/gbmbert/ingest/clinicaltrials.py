"""Read-only ClinicalTrials.gov v2 ingestion for GBM-AI trial provenance."""

from __future__ import annotations

import argparse
import json
import logging
import time
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

LOGGER = logging.getLogger(__name__)
CLINICALTRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
DEFAULT_TRIALS_JSONL_PATH = Path("data/raw/clinicaltrials_gbm.jsonl")


class ClinicalTrialsIngestionError(RuntimeError):
    """Raised when ClinicalTrials.gov data cannot be requested or parsed."""


class ClinicalTrialRecord(BaseModel):
    """A descriptive ClinicalTrials.gov record with registry provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nct_id: str = Field(..., min_length=1)
    brief_title: str = ""
    official_title: str = ""
    overall_status: str = ""
    phases: list[str] = Field(default_factory=list)
    study_type: str = ""
    conditions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    start_date: str = ""
    primary_completion_date: str = ""
    completion_date: str = ""
    enrollment_count: int | None = None
    sponsor: str = ""
    has_results: bool = False
    last_update_posted: str = ""
    source_url: str = ""
    query: str = ""

    @field_validator("nct_id")
    @classmethod
    def nct_id_must_look_like_registry_id(cls, value: str) -> str:
        value = value.strip()
        if not value.upper().startswith("NCT"):
            raise ValueError("nct_id must start with NCT")
        return value


def search_clinical_trials(
    *,
    condition: str = "glioblastoma",
    query: str = "",
    page_size: int = 25,
    max_records: int = 100,
    overall_status: str | None = None,
) -> list[dict[str, Any]]:
    """Search ClinicalTrials.gov v2 studies and return raw study payloads."""

    if not condition.strip() and not query.strip():
        raise ValueError("condition or query is required")
    if page_size < 1 or page_size > 1000:
        raise ValueError("page_size must be between 1 and 1000")
    if max_records < 1:
        raise ValueError("max_records must be at least 1")

    studies: list[dict[str, Any]] = []
    page_token: str | None = None
    while len(studies) < max_records:
        params: dict[str, Any] = {
            "format": "json",
            "pageSize": min(page_size, max_records - len(studies)),
        }
        if condition.strip():
            params["query.cond"] = condition.strip()
        if query.strip():
            params["query.term"] = query.strip()
        if overall_status:
            params["filter.overallStatus"] = overall_status
        if page_token:
            params["pageToken"] = page_token

        payload = _request_json(CLINICALTRIALS_BASE_URL, params)
        studies.extend(payload.get("studies", []))
        page_token = payload.get("nextPageToken") or payload.get("pageToken")
        if not page_token:
            break
        time.sleep(0.2)
    return studies[:max_records]


def fetch_clinical_trial(nct_id: str) -> dict[str, Any]:
    """Fetch one ClinicalTrials.gov v2 study by NCT ID."""

    normalized = nct_id.strip()
    if not normalized:
        raise ValueError("nct_id is required")
    return _request_json(f"{CLINICALTRIALS_BASE_URL}/{urllib.parse.quote(normalized)}", {"format": "json"})


def parse_clinical_trial(study: dict[str, Any], *, query: str = "") -> ClinicalTrialRecord:
    """Normalize a ClinicalTrials.gov v2 study payload into a descriptive record."""

    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    conditions = protocol.get("conditionsModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})

    nct_id = str(identification.get("nctId", ""))
    lead_sponsor = sponsor.get("leadSponsor", {})
    enrollment = design.get("enrollmentInfo", {})
    return ClinicalTrialRecord(
        nct_id=nct_id,
        brief_title=str(identification.get("briefTitle", "")),
        official_title=str(identification.get("officialTitle", "")),
        overall_status=str(status.get("overallStatus", "")),
        phases=[str(phase) for phase in design.get("phases", [])],
        study_type=str(design.get("studyType", "")),
        conditions=[str(condition) for condition in conditions.get("conditions", [])],
        interventions=[
            str(item.get("name", ""))
            for item in arms.get("interventions", [])
            if item.get("name")
        ],
        start_date=_date_value(status.get("startDateStruct", {})),
        primary_completion_date=_date_value(status.get("primaryCompletionDateStruct", {})),
        completion_date=_date_value(status.get("completionDateStruct", {})),
        enrollment_count=enrollment.get("count"),
        sponsor=str(lead_sponsor.get("name", "")),
        has_results=bool(study.get("hasResults", False)),
        last_update_posted=_date_value(status.get("lastUpdatePostDateStruct", {})),
        source_url=f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
        query=query,
    )


def parse_clinical_trials(studies: Iterable[dict[str, Any]], *, query: str = "") -> list[ClinicalTrialRecord]:
    """Parse multiple raw ClinicalTrials.gov studies."""

    return [parse_clinical_trial(study, query=query) for study in studies]


def save_trials_jsonl(
    records: Iterable[ClinicalTrialRecord],
    path: str | Path = DEFAULT_TRIALS_JSONL_PATH,
) -> Path:
    """Save normalized ClinicalTrials.gov records as newline-delimited JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json())
            handle.write("\n")
    LOGGER.info("Saved ClinicalTrials.gov JSONL records to %s", output_path)
    return output_path


def search_and_save_clinical_trials(
    *,
    condition: str = "glioblastoma",
    query: str = "",
    output: str | Path = DEFAULT_TRIALS_JSONL_PATH,
    page_size: int = 25,
    max_records: int = 100,
    overall_status: str | None = None,
) -> Path:
    """Search ClinicalTrials.gov, normalize records, and write JSONL."""

    raw = search_clinical_trials(
        condition=condition,
        query=query,
        page_size=page_size,
        max_records=max_records,
        overall_status=overall_status,
    )
    query_label = " | ".join(part for part in [condition.strip(), query.strip()] if part)
    return save_trials_jsonl(parse_clinical_trials(raw, query=query_label), output)


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params, doseq=True)
    request_url = f"{url}?{encoded}" if encoded else url
    LOGGER.debug("Requesting ClinicalTrials.gov URL %s", request_url)
    try:
        with urllib.request.urlopen(request_url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ClinicalTrialsIngestionError("ClinicalTrials.gov returned invalid JSON") from exc
    except OSError as exc:
        raise ClinicalTrialsIngestionError("ClinicalTrials.gov request failed") from exc


def _date_value(date_struct: dict[str, Any]) -> str:
    return str(date_struct.get("date", "") or "")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search ClinicalTrials.gov v2 for read-only GBM trial registry records."
    )
    parser.add_argument("--condition", default="glioblastoma")
    parser.add_argument("--query", default="")
    parser.add_argument("--output", type=Path, default=DEFAULT_TRIALS_JSONL_PATH)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--max-records", type=int, default=100)
    parser.add_argument("--overall-status")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    search_and_save_clinical_trials(
        condition=args.condition,
        query=args.query,
        output=args.output,
        page_size=args.page_size,
        max_records=args.max_records,
        overall_status=args.overall_status,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
