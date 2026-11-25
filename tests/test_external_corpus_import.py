import json
from pathlib import Path

from gbmbert.training.external_corpus_import import (
    EXTERNAL_SOURCE_TYPE,
    import_external_corpus,
    read_bc5cdr_tner,
    read_biored_bioc,
    read_ebm_nlp,
    read_treatment_stub_jsonl,
)

# tner/bc5cdr tag scheme: O=0, B-Chemical=1, B-Disease=2, I-Disease=3, I-Chemical=4
_FIXTURE = [
    {"tokens": ["Naloxone", "reverses", "clonidine", "."], "tags": [1, 0, 1, 0]},
    {"tokens": ["The", "hypotensive", "renal", "failure", "after", "aspirin"], "tags": [0, 2, 3, 3, 0, 1]},
]

_BIORED_FIXTURE = {
    "source": "BioRED",
    "date": "2022",
    "key": "fixture",
    "documents": [
        {
            "id": "14510914",
            "passages": [
                {
                    "offset": 0,
                    "text": "Congenital hypothyroidism due to NIS.",
                    "annotations": [
                        {
                            "id": "0",
                            "infons": {"identifier": "D003409", "type": "DiseaseOrPhenotypicFeature"},
                            "text": "Congenital hypothyroidism",
                            "locations": [{"offset": 0, "length": 25}],
                        },
                        {
                            "id": "1",
                            "infons": {"identifier": "6528", "type": "GeneOrGeneProduct"},
                            "text": "NIS",
                            "locations": [{"offset": 33, "length": 3}],
                        },
                    ],
                },
                {
                    "offset": 38,
                    "text": "Cell study of HeLa with aspirin variant c.1A>G.",
                    "annotations": [
                        {
                            "id": "2",
                            "infons": {"identifier": "CVCL_0030", "type": "CellLine"},
                            "text": "HeLa",
                            "locations": [{"offset": 52, "length": 4}],
                        },
                        {
                            "id": "3",
                            "infons": {"identifier": "D001241", "type": "ChemicalEntity"},
                            "text": "aspirin",
                            "locations": [{"offset": 62, "length": 7}],
                        },
                        {
                            "id": "4",
                            "infons": {"identifier": "c|SUB|A|1|G|", "type": "SequenceVariant"},
                            "text": "c.1A>G",
                            "locations": [{"offset": 78, "length": 6}],
                        },
                        {
                            "id": "5",
                            "infons": {"identifier": "9606", "type": "OrganismTaxon"},
                            "text": "study",
                            "locations": [{"offset": 43, "length": 5}],
                        },
                    ],
                },
            ],
            "relations": [
                {
                    "id": "R0",
                    "infons": {
                        "entity1": "6528",
                        "entity2": "D003409",
                        "type": "Association",
                        "novel": "Novel",
                    },
                },
                {
                    "id": "R1",
                    "infons": {
                        "entity1": "D001241",
                        "entity2": "6528",
                        "type": "Positive_Correlation",
                        "novel": "No",
                    },
                },
            ],
        }
    ],
}


def _write_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "bc5cdr_train.json"
    path.write_text("".join(json.dumps(r) + "\n" for r in _FIXTURE), encoding="utf-8")
    return path


def _write_biored_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "Dev.BioC.JSON"
    path.write_text(json.dumps(_BIORED_FIXTURE), encoding="utf-8")
    return path


def test_read_bc5cdr_reconstructs_spans_and_offsets(tmp_path: Path) -> None:
    docs = read_bc5cdr_tner(_write_fixture(tmp_path))

    assert len(docs) == 2
    # Doc 0: two single-token Chemicals.
    d0 = docs[0]
    chems = [(e.text, e.label) for e in d0.entities]
    assert chems == [("Naloxone", "Chemical"), ("clonidine", "Chemical")]
    # Offsets index into the space-joined text.
    e0 = d0.entities[0]
    assert d0.text[e0.start : e0.end] == "Naloxone"
    # Doc 1: a multi-token Disease span (B-Disease, I-Disease...) then a Chemical.
    d1 = docs[1]
    spans = [(e.text, e.label) for e in d1.entities]
    assert ("hypotensive renal failure", "Disease") in spans
    assert ("aspirin", "Chemical") in spans
    dis = next(e for e in d1.entities if e.label == "Disease")
    assert d1.text[dis.start : dis.end] == "hypotensive renal failure"


def test_import_maps_bc5cdr_labels_to_project_scheme(tmp_path: Path) -> None:
    crosswalk = tmp_path / "crosswalk.json"
    crosswalk.write_text(
        json.dumps(
            {
                "corpora": {
                    "bc5cdr": {
                        "reader": "bc5cdr_tner",
                        "license": "NLM research use",
                        "entity_label_map": {"Chemical": "DRUG", "Disease": "DISEASE"},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "gold_entities.jsonl"

    report = import_external_corpus(
        corpus="bc5cdr",
        input_path=_write_fixture(tmp_path),
        output_path=out,
        crosswalk_path=crosswalk,
    )

    assert report.document_count == 2
    assert report.project_entity_label_counts == {"DISEASE": 1, "DRUG": 3}
    assert report.dropped_entity_label_counts == {}
    assert report.source_type == EXTERNAL_SOURCE_TYPE
    assert report.license == "NLM research use"
    assert report.relation_count == 0
    assert report.relations_output_path == ""

    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert all(r["source_corpus"] == "bc5cdr" and r["source_type"] == EXTERNAL_SOURCE_TYPE for r in records)
    assert {e["label"] for r in records for e in r["entities"]} == {"DRUG", "DISEASE"}
    # Output matches the gold_entities schema consumed by the gold pack.
    sample = records[0]["entities"][0]
    assert set(sample) == {"confidence", "end", "label", "normalized_text", "start", "text"}


def test_import_drops_unmapped_labels_with_warning(tmp_path: Path) -> None:
    crosswalk = tmp_path / "crosswalk.json"
    # Only map Chemical; Disease is intentionally left unmapped -> dropped + warned.
    crosswalk.write_text(
        json.dumps(
            {"corpora": {"bc5cdr": {"reader": "bc5cdr_tner", "entity_label_map": {"Chemical": "DRUG"}}}}
        ),
        encoding="utf-8",
    )
    out = tmp_path / "gold_entities.jsonl"

    report = import_external_corpus(corpus="bc5cdr", input_path=_write_fixture(tmp_path), output_path=out, crosswalk_path=crosswalk)

    assert report.project_entity_label_counts == {"DRUG": 3}
    assert report.dropped_entity_label_counts == {"Disease": 1}
    assert any("dropped unmapped" in w for w in report.warnings)


def test_read_biored_bioc_preserves_pmids_offsets_and_relations(tmp_path: Path) -> None:
    docs = read_biored_bioc(_write_biored_fixture(tmp_path))

    assert len(docs) == 1
    doc = docs[0]
    assert doc.source_pmid == "14510914"
    assert doc.doc_id == "14510914"
    # Offsets reconstruct against the passage buffer.
    gene = next(e for e in doc.entities if e.label == "GeneOrGeneProduct")
    assert doc.text[gene.start : gene.end] == "NIS"
    assert gene.identifier == "6528"
    assert len(doc.relations) == 2
    assert {r.relation_type for r in doc.relations} == {"Association", "Positive_Correlation"}


def test_import_maps_biored_entities_and_relations(tmp_path: Path) -> None:
    crosswalk = tmp_path / "crosswalk.json"
    crosswalk.write_text(
        json.dumps(
            {
                "corpora": {
                    "biored": {
                        "reader": "biored_bioc",
                        "license": "BioRED research use",
                        "entity_label_map": {
                            "GeneOrGeneProduct": "GENE",
                            "CellLine": "CELL_TYPE",
                            "ChemicalEntity": "DRUG",
                            "DiseaseOrPhenotypicFeature": "DISEASE",
                            "SequenceVariant": "BIOMARKER",
                        },
                        "relation_label_map": {
                            "Association": "ASSOCIATED_WITH",
                            "Positive_Correlation": "PREDICTS",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "gold_entities.jsonl"
    rel_out = tmp_path / "gold_relations.jsonl"

    report = import_external_corpus(
        corpus="biored",
        input_path=_write_biored_fixture(tmp_path),
        output_path=out,
        relations_output_path=rel_out,
        crosswalk_path=crosswalk,
    )

    assert report.document_count == 1
    assert report.project_entity_label_counts == {
        "BIOMARKER": 1,
        "CELL_TYPE": 1,
        "DISEASE": 1,
        "DRUG": 1,
        "GENE": 1,
    }
    assert report.dropped_entity_label_counts == {"OrganismTaxon": 1}
    assert report.project_relation_label_counts == {"ASSOCIATED_WITH": 1, "PREDICTS": 1}
    assert report.relation_count == 2
    assert report.relations_output_path == str(rel_out)

    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert records[0]["pmid"] == "14510914"
    assert {e["label"] for e in records[0]["entities"]} == {"GENE", "CELL_TYPE", "DRUG", "DISEASE", "BIOMARKER"}

    relations = [json.loads(line) for line in rel_out.read_text(encoding="utf-8").splitlines()]
    assert len(relations) == 2
    assert all(r["source_corpus"] == "biored" and r["source_type"] == EXTERNAL_SOURCE_TYPE for r in relations)
    assert {r["label"] for r in relations} == {"ASSOCIATED_WITH", "PREDICTS"}
    assert any(r["head"].startswith("GENE:") and r["tail"].startswith("DISEASE:") for r in relations)


def test_read_biored_bioc_directory(tmp_path: Path) -> None:
    directory = tmp_path / "biored"
    directory.mkdir()
    (directory / "Dev.BioC.JSON").write_text(json.dumps(_BIORED_FIXTURE), encoding="utf-8")
    docs = read_biored_bioc(directory)
    assert len(docs) == 1
    assert docs[0].source_pmid == "14510914"


def test_repo_crosswalk_documents_biored_onboarding() -> None:
    crosswalk = json.loads(Path("configs/extraction/external_corpus_crosswalk.json").read_text(encoding="utf-8"))

    assert crosswalk["corpora"]["bc5cdr"]["entity_label_map"] == {"Chemical": "DRUG", "Disease": "DISEASE"}
    biored = crosswalk["corpora"]["biored"]
    assert biored["reader"] == "biored_bioc"
    assert biored["entity_label_map"]["GeneOrGeneProduct"] == "GENE"
    assert biored["entity_label_map"]["CellLine"] == "CELL_TYPE"
    assert biored["entity_label_map"]["SequenceVariant"] == "BIOMARKER"
    assert biored["relation_label_map"]["Association"] == "ASSOCIATED_WITH"
    assert "ftp.ncbi.nlm.nih.gov/pub/lu/BioRED" in biored["source"]
    ebm = crosswalk["corpora"]["ebm_nlp"]
    assert ebm["reader"] == "ebm_nlp"
    assert ebm["entity_label_map"]["Intervention"] == "TREATMENT"
    assert ebm["entity_label_map"]["Outcome"] == "OUTCOME"
    assert "bepnye/EBM-NLP" in ebm["source"]
    treatment = crosswalk["corpora"]["treatment_stub"]
    assert treatment["reader"] == "treatment_stub_jsonl"
    assert treatment["entity_label_map"]["Intervention"] == "TREATMENT"
    for label in ("GENE", "TREATMENT", "OUTCOME", "BIOMARKER", "CELL_TYPE"):
        assert label in crosswalk["future_project_labels"]


def test_treatment_stub_import_maps_intervention_to_treatment(tmp_path: Path) -> None:
    fixture = Path("data/examples/treatment_stub_sample.jsonl")
    docs = read_treatment_stub_jsonl(fixture)
    assert len(docs) == 2
    assert any(entity.label == "Intervention" for entity in docs[0].entities)

    out = tmp_path / "gold_entities.jsonl"
    report = import_external_corpus(
        corpus="treatment_stub",
        input_path=fixture,
        output_path=out,
    )

    assert report.document_count == 2
    assert report.project_entity_label_counts.get("TREATMENT", 0) >= 3
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert all(record["source_type"] == EXTERNAL_SOURCE_TYPE for record in records)
    assert {entity["label"] for record in records for entity in record["entities"]} == {"TREATMENT"}


def test_ebm_nlp_reader_maps_intervention_and_outcome_spans() -> None:
    fixture = Path("data/examples/ebm_nlp_sample")
    docs = read_ebm_nlp(fixture)

    assert len(docs) >= 3
    assert any(doc.source_pmid == "29097493" for doc in docs)
    assert all(doc.source_pmid and doc.source_pmid.isdigit() for doc in docs)
    assert any(entity.label == "Intervention" for doc in docs for entity in doc.entities)
    assert any(entity.label == "Outcome" for doc in docs for entity in doc.entities)
    for doc in docs:
        for entity in doc.entities:
            assert doc.text[entity.start : entity.end] == entity.text


def test_ebm_nlp_import_maps_treatment_and_outcome(tmp_path: Path) -> None:
    out = tmp_path / "gold_entities.jsonl"
    report = import_external_corpus(
        corpus="ebm_nlp",
        input_path=Path("data/examples/ebm_nlp_sample"),
        output_path=out,
    )

    assert report.document_count >= 3
    assert report.reader == "ebm_nlp"
    assert report.project_entity_label_counts.get("TREATMENT", 0) >= 1
    assert report.project_entity_label_counts.get("OUTCOME", 0) >= 1
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert all(record["source_corpus"] == "ebm_nlp" for record in records)
    assert all(record["source_type"] == EXTERNAL_SOURCE_TYPE for record in records)
    labels = {entity["label"] for record in records for entity in record["entities"]}
    assert labels == {"TREATMENT", "OUTCOME"}
    assert any(record["pmid"] == "29097493" for record in records)


def test_ebm_nlp_prefers_gold_over_crowd(tmp_path: Path) -> None:
    root = tmp_path / "ebm"
    documents = root / "documents"
    gold = root / "annotations" / "aggregated" / "starting_spans" / "interventions" / "test" / "gold"
    crowd = root / "annotations" / "aggregated" / "starting_spans" / "interventions" / "test" / "crowd"
    documents.mkdir(parents=True)
    gold.mkdir(parents=True)
    crowd.mkdir(parents=True)
    (documents / "1.tokens").write_text("drug\nA\n", encoding="utf-8")
    (gold / "1.AGGREGATED.ann").write_text("1\n0\n", encoding="utf-8")
    (crowd / "1.AGGREGATED.ann").write_text("0\n1\n", encoding="utf-8")

    docs = read_ebm_nlp(root)

    assert len(docs) == 1
    assert len(docs[0].entities) == 1
    entity = docs[0].entities[0]
    assert entity.text == "drug"
    assert entity.label == "Intervention"
    assert entity.start == 0
    assert entity.end == 4
