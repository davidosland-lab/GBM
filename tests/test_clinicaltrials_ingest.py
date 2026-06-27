import json
from pathlib import Path

from gbmbert.ingest import clinicaltrials
from gbmbert.ingest.clinicaltrials import (
    ClinicalTrialRecord,
    parse_clinical_trial,
    save_trials_jsonl,
    search_clinical_trials,
)


def sample_study(nct_id: str = "NCT12345678") -> dict:
    return {
        "hasResults": True,
        "protocolSection": {
            "identificationModule": {
                "nctId": nct_id,
                "briefTitle": "Glioblastoma trial",
                "officialTitle": "A Study in Glioblastoma",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2026-01-01"},
                "primaryCompletionDateStruct": {"date": "2027-01-01"},
                "completionDateStruct": {"date": "2028-01-01"},
                "lastUpdatePostDateStruct": {"date": "2026-06-01"},
            },
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 42},
            },
            "conditionsModule": {"conditions": ["Glioblastoma"]},
            "armsInterventionsModule": {
                "interventions": [{"name": "Temozolomide"}, {"name": "Pembrolizumab"}]
            },
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Example Sponsor"}},
        },
    }


def test_parse_clinical_trial_returns_descriptive_registry_record() -> None:
    record = parse_clinical_trial(sample_study(), query="glioblastoma")

    assert record.nct_id == "NCT12345678"
    assert record.overall_status == "RECRUITING"
    assert record.phases == ["PHASE2"]
    assert record.interventions == ["Temozolomide", "Pembrolizumab"]
    assert record.enrollment_count == 42
    assert record.source_url == "https://clinicaltrials.gov/study/NCT12345678"
    assert record.query == "glioblastoma"


def test_search_clinical_trials_uses_v2_pagination(monkeypatch) -> None:
    calls = []

    def fake_request(url: str, params: dict) -> dict:
        calls.append((url, params))
        if "pageToken" not in params:
            return {"studies": [sample_study("NCT00000001")], "nextPageToken": "next"}
        return {"studies": [sample_study("NCT00000002")]}

    monkeypatch.setattr(clinicaltrials, "_request_json", fake_request)

    studies = search_clinical_trials(condition="glioblastoma", page_size=1, max_records=2)

    assert [study["protocolSection"]["identificationModule"]["nctId"] for study in studies] == [
        "NCT00000001",
        "NCT00000002",
    ]
    assert calls[0][1]["query.cond"] == "glioblastoma"
    assert calls[1][1]["pageToken"] == "next"


def test_save_trials_jsonl_writes_records(tmp_path: Path) -> None:
    path = tmp_path / "trials.jsonl"
    record = ClinicalTrialRecord(nct_id="NCT12345678", brief_title="GBM trial")

    save_trials_jsonl([record], path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["nct_id"] == "NCT12345678"
    assert payload["brief_title"] == "GBM trial"
