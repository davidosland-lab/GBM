import json
from pathlib import Path

from gbmbert.ingest.clinicaltrials import ClinicalTrialRecord
from gbmbert.knowledge_graph.schema import NodeLabel, RelationType
from gbmbert.knowledge_graph.trials import (
    ClinicalTrialGraphRecord,
    build_trial_graph_records,
    build_trial_graph_records_from_jsonl,
)


def trial_record() -> ClinicalTrialRecord:
    return ClinicalTrialRecord(
        nct_id="NCT12345678",
        brief_title="Glioblastoma immunotherapy trial",
        overall_status="RECRUITING",
        phases=["PHASE2"],
        study_type="INTERVENTIONAL",
        conditions=["Glioblastoma"],
        interventions=["Temozolomide", "Pembrolizumab"],
        enrollment_count=42,
        sponsor="Example Sponsor",
        source_url="https://clinicaltrials.gov/study/NCT12345678",
        query="glioblastoma",
    )


def test_build_trial_graph_records_preserves_nct_provenance() -> None:
    record = next(build_trial_graph_records([trial_record()]))

    assert record.nct_id == "NCT12345678"
    assert record.trial_properties["nct_id"] == "NCT12345678"
    assert record.trial_properties["overall_status"] == "RECRUITING"
    assert [(node.label, node.key_value) for node in record.nodes] == [
        (NodeLabel.DISEASE, "Glioblastoma"),
        (NodeLabel.TREATMENT, "Temozolomide"),
        (NodeLabel.TREATMENT, "Pembrolizumab"),
    ]
    assert [relation.relation for relation in record.relations] == [
        RelationType.ASSOCIATED_WITH,
        RelationType.ASSOCIATED_WITH,
        RelationType.ASSOCIATED_WITH,
    ]
    assert {relation.source_id for relation in record.relations} == {"NCT12345678"}
    assert record.relations[0].properties["source"] == "clinicaltrials.gov"


def test_build_trial_graph_records_from_jsonl_roundtrip(tmp_path: Path) -> None:
    trials_path = tmp_path / "trials.jsonl"
    output_path = tmp_path / "trial_graph_records.jsonl"
    trials_path.write_text(trial_record().model_dump_json() + "\n", encoding="utf-8")

    saved = build_trial_graph_records_from_jsonl(trials_path, output_path)
    loaded = [
        ClinicalTrialGraphRecord.model_validate(json.loads(line))
        for line in saved.read_text(encoding="utf-8").splitlines()
    ]

    assert saved == output_path
    assert loaded[0].nct_id == "NCT12345678"
    assert len(loaded[0].relations) == 3
