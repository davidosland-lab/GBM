import json
from pathlib import Path

from gbmbert.annotation.schema import EntityType, Paper
from gbmbert.extraction.entities import entity_from_model_output, normalize_label
from gbmbert.extraction.io import load_entity_jsonl, load_pubmed_jsonl, save_entity_jsonl
from gbmbert.extraction.pipeline import BiomedicalNERPipeline, paper_to_source_text, split_text_chunks


def test_normalize_label_maps_model_labels_to_supported_types() -> None:
    assert normalize_label("Gene") is EntityType.GENE
    assert normalize_label("B-Chemical") is EntityType.DRUG
    assert normalize_label("cell_line") is EntityType.CELL_TYPE
    assert normalize_label("cell_state") is EntityType.CELL_STATE
    assert normalize_label("delivery_modifier") is EntityType.DELIVERY_MODIFIER
    assert normalize_label("B-Medication") is EntityType.DRUG
    assert normalize_label("I-Disease_disorder") is EntityType.DISEASE
    assert normalize_label("Therapeutic_procedure") is EntityType.TREATMENT
    assert normalize_label("Lab_value") is EntityType.BIOMARKER
    assert normalize_label("Sign_symptom") is EntityType.DISEASE
    assert normalize_label("not-a-real-label") is EntityType.UNKNOWN


def test_entity_from_model_output_uses_offsets_and_normalizes_text() -> None:
    text = "MGMT methylation predicts TMZ response."
    entity = entity_from_model_output(
        {"word": "TMZ", "entity_group": "Chemical", "score": 0.99, "start": 26, "end": 29},
        text,
    )

    assert entity.text == "TMZ"
    assert entity.label is EntityType.DRUG
    assert entity.normalized_text == "temozolomide"
    assert entity.confidence == 0.99


def test_biomedical_ner_pipeline_extracts_entities_with_fake_model() -> None:
    paper = Paper(
        pmid="12345678",
        title="EGFR amplification in GBM",
        abstract="TMZ is used in glioblastoma research.",
    )

    def fake_pipeline(text: str) -> list[dict[str, object]]:
        assert "EGFR amplification" in text
        return [
            {"word": "EGFR", "entity_group": "Gene", "score": 0.95, "start": 0, "end": 4},
            {"word": "GBM", "entity_group": "Disease", "score": 0.9, "start": 22, "end": 25},
        ]

    extractor = BiomedicalNERPipeline(ner_pipeline=fake_pipeline)
    result = extractor.extract_from_paper(paper)

    assert result.pmid == "12345678"
    assert len(result.entities) == 2
    assert result.entities[0].normalized_text == "EGFR"
    assert result.entities[1].normalized_text == "glioblastoma"


def test_paper_to_source_text_combines_title_and_abstract() -> None:
    paper = Paper(pmid="12345678", title=" Title ", abstract=" Abstract\ntext ")

    assert paper_to_source_text(paper) == "Title Abstract text"


def test_split_text_chunks_preserves_source_offsets() -> None:
    text = "alpha beta gamma delta epsilon"

    chunks = list(split_text_chunks(text, max_words=3, overlap_words=1))

    assert chunks == [
        (0, "alpha beta gamma"),
        (11, "gamma delta epsilon"),
    ]


def test_biomedical_ner_pipeline_chunks_and_restores_offsets() -> None:
    title = "alpha beta gamma delta epsilon zeta eta"
    paper = Paper(pmid="12345678", title=title)
    calls: list[str] = []

    def fake_pipeline(text: str) -> list[dict[str, object]]:
        calls.append(text)
        outputs: list[dict[str, object]] = []
        if "gamma" in text:
            score = 0.1 if text.startswith("alpha") else 0.8
            start = text.index("gamma")
            outputs.append(
                {
                    "word": "gamma",
                    "entity_group": "Disease_disorder",
                    "score": score,
                    "start": start,
                    "end": start + len("gamma"),
                }
            )
        if "zeta" in text:
            start = text.index("zeta")
            outputs.append(
                {
                    "word": "zeta",
                    "entity_group": "Therapeutic_procedure",
                    "score": 0.7,
                    "start": start,
                    "end": start + len("zeta"),
                }
            )
        return outputs

    extractor = BiomedicalNERPipeline(
        ner_pipeline=fake_pipeline,
        max_chunk_words=3,
        chunk_overlap_words=1,
    )
    result = extractor.extract_from_paper(paper)

    assert calls == [
        "alpha beta gamma",
        "gamma delta epsilon",
        "epsilon zeta eta",
    ]
    observed_entities = [
        (entity.text, entity.label, entity.start, entity.confidence) for entity in result.entities
    ]
    assert observed_entities == [
        ("gamma", EntityType.DISEASE, title.index("gamma"), 0.8),
        ("zeta", EntityType.TREATMENT, title.index("zeta"), 0.7),
    ]


def test_pubmed_jsonl_loads_and_entity_jsonl_writes(tmp_path: Path) -> None:
    input_path = tmp_path / "pubmed.jsonl"
    output_path = tmp_path / "entities.jsonl"
    input_record = {
        "pmid": "12345678",
        "title": "MGMT methylation",
        "abstract": "TMZ response in glioblastoma.",
        "journal": "Research Journal",
        "publication_date": "2024",
        "mesh_terms": ["Glioblastoma"],
    }
    input_path.write_text(json.dumps(input_record) + "\n", encoding="utf-8")

    papers = list(load_pubmed_jsonl(input_path))
    extractor = BiomedicalNERPipeline(
        ner_pipeline=lambda text: [
            {"word": "MGMT", "entity_group": "Gene", "score": 0.92, "start": 0, "end": 4}
        ]
    )
    results = [extractor.extract_from_paper(papers[0])]
    saved_path = save_entity_jsonl(results, output_path)
    reloaded = list(load_entity_jsonl(saved_path))

    assert papers[0].pmid == "12345678"
    assert saved_path.exists()
    assert reloaded[0].model_dump(mode="json") == {
        "pmid": "12345678",
        "entities": [
            {
                "text": "MGMT",
                "label": "GENE",
                "start": 0,
                "end": 4,
                "confidence": 0.92,
                "normalized_text": "MGMT",
            }
        ],
    }
