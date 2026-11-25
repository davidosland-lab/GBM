import json
from pathlib import Path

from gbmbert.training.evaluation import evaluate_bio_spans
from gbmbert.training.ner_bio import (
    align_bio_labels,
    bio_label_map_is_bio,
    build_ner_bio_pack,
    spans_from_bio_ids,
)


def test_align_and_decode_bio_spans() -> None:
    label_to_id = {"O": 0, "B-DISEASE": 1, "I-DISEASE": 2, "B-DRUG": 3, "I-DRUG": 4}
    text = "temozolomide treats glioblastoma patients"
    # Fake offsets approximating whitespace tokens.
    offsets = [(0, 0), (0, 12), (13, 19), (20, 32), (33, 41), (0, 0)]
    entities = [{"text": "temozolomide", "label": "DRUG", "start": 0, "end": 12}]
    labels = align_bio_labels(text=text, entities=entities, offset_mapping=offsets, label_to_id=label_to_id)

    assert labels[0] == -100
    assert labels[1] == label_to_id["B-DRUG"]
    assert labels[2] == label_to_id["O"]
    spans = spans_from_bio_ids(labels, {index: label for label, index in label_to_id.items()})
    assert spans == [(1, 1, "DRUG")]


def test_bio_label_map_detection() -> None:
    assert bio_label_map_is_bio({"O": 0, "B-GENE": 1, "I-GENE": 2})
    assert not bio_label_map_is_bio({"GENE": 0, "DRUG": 1})


def test_evaluate_bio_spans_exact_match() -> None:
    report = evaluate_bio_spans(
        task="ner",
        true_spans_by_doc=[[(0, 1, "DRUG"), (3, 4, "DISEASE")]],
        predicted_spans_by_doc=[[(0, 1, "DRUG"), (5, 5, "GENE")]],
        entity_types=["DRUG", "DISEASE", "GENE"],
    )

    by_label = {item.label: item for item in report.labels}
    assert report.examples == 2
    assert by_label["DRUG"].f1 == 1.0
    assert by_label["DISEASE"].recall == 0.0
    assert by_label["GENE"].precision == 0.0


def test_build_ner_bio_pack_uses_embedded_text_without_pubmed(tmp_path: Path) -> None:
    entities = tmp_path / "entities.jsonl"
    text = "Radiotherapy plus temozolomide after resection"
    entities.write_text(
        json.dumps(
            {
                "pmid": "939970",
                "source_corpus": "ebm_nlp",
                "text": text,
                "entities": [
                    {"text": "Radiotherapy", "label": "TREATMENT", "start": 0, "end": 12},
                    {"text": "temozolomide", "label": "TREATMENT", "start": 19, "end": 31},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_ner_bio_pack(
        output_dir=tmp_path / "pack",
        entity_jsonl=[entities],
        pubmed_jsonl=[],
        seed=13,
    )

    assert report.document_count == 1
    assert report.entity_count == 2
    assert report.entity_type_counts["TREATMENT"] == 2
    split_rows = []
    for split in ("train", "validation", "test"):
        path = tmp_path / "pack" / "annotation_splits" / f"ner_{split}.jsonl"
        split_rows.extend(
            [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        )
    assert len(split_rows) == 1
    assert split_rows[0]["text"] == text
    assert split_rows[0]["entities"][0]["text"] == "Radiotherapy"


def test_build_ner_bio_pack_writes_splits(tmp_path: Path) -> None:
    entities = tmp_path / "entities.jsonl"
    pubmed = tmp_path / "pubmed.jsonl"
    entities.write_text(
        json.dumps(
            {
                "pmid": "1",
                "entities": [{"text": "glioblastoma", "label": "DISEASE", "start": 0, "end": 12}],
            }
        )
        + "\n"
        + json.dumps(
            {
                "pmid": "2",
                "entities": [{"text": "temozolomide", "label": "DRUG", "start": 13, "end": 25}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    text1 = "glioblastoma remains a challenging primary brain tumor in adults"
    text2 = "Drug temozolomide improves survival in recurrent disease settings"
    pubmed.write_text(
        json.dumps({"pmid": "1", "title": "glioblastoma", "abstract": "remains a challenging primary brain tumor in adults"})
        + "\n"
        + json.dumps({"pmid": "2", "title": "Drug", "abstract": "temozolomide improves survival in recurrent disease settings"})
        + "\n"
        + json.dumps({"pmid": "3", "title": "Extra", "abstract": "unused filler abstract text for length checks"})
        + "\n",
        encoding="utf-8",
    )
    start2 = text2.find("temozolomide")
    entities.write_text(
        json.dumps(
            {
                "pmid": "1",
                "entities": [{"text": "glioblastoma", "label": "DISEASE", "start": 0, "end": 12}],
            }
        )
        + "\n"
        + json.dumps(
            {
                "pmid": "2",
                "entities": [{"text": "temozolomide", "label": "DRUG", "start": start2, "end": start2 + 12}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert text1.startswith("glioblastoma")

    report = build_ner_bio_pack(
        output_dir=tmp_path / "pack",
        entity_jsonl=[entities],
        pubmed_jsonl=[pubmed],
        seed=13,
        oversample_sparse_train=1,
    )

    assert report.document_count == 2
    assert report.entity_count == 2
    assert (tmp_path / "pack" / "annotation_splits" / "ner_train.jsonl").exists()
    label_map = json.loads((tmp_path / "pack" / "label_maps" / "ner_label_map.json").read_text(encoding="utf-8"))
    assert label_map["encoding"] == "bio"
    assert "O" in label_map["label_to_id"]
    assert "B-DISEASE" in label_map["label_to_id"]


def test_build_ner_bio_pack_cleans_unknown_and_remaps_pathway_genes(tmp_path: Path) -> None:
    entities = tmp_path / "entities.jsonl"
    text = "EGFR signaling and putative markers in mesenchymal glioblastoma"
    entities.write_text(
        json.dumps(
            {
                "pmid": "99",
                "text": text,
                "entities": [
                    {"text": "EGFR", "label": "PATHWAY", "start": 0, "end": 4},
                    {"text": "putative", "label": "UNKNOWN", "start": 19, "end": 27},
                    {"text": "mesenchymal", "label": "CELL_STATE", "start": 39, "end": 50},
                    {"text": "glioblastoma", "label": "DISEASE", "start": 51, "end": 63},
                ],
            }
        )
        + "\n"
        + json.dumps(
            {
                "pmid": "100",
                "text": "PI3K/AKT pathway drives invasive glioma growth patterns here",
                "entities": [
                    {"text": "PI3K/AKT", "label": "PATHWAY", "start": 0, "end": 8},
                    {"text": "invasive", "label": "CELL_STATE", "start": 24, "end": 32},
                ],
            }
        )
        + "\n"
        + json.dumps(
            {
                "pmid": "101",
                "text": "Phase II trial enrolled patients with recurrent disease only",
                "entities": [
                    {"text": "Phase II", "label": "TRIAL_PHASE", "start": 0, "end": 8},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_ner_bio_pack(
        output_dir=tmp_path / "pack",
        entity_jsonl=[entities],
        pubmed_jsonl=[],
        seed=13,
        oversample_sparse_train=1,
    )

    assert "UNKNOWN" not in report.entity_type_counts
    assert report.entity_type_counts["GENE"] == 1
    assert report.entity_type_counts["PATHWAY"] == 1
    assert any("dropped" in warning and "UNKNOWN" in warning for warning in report.warnings)
    assert any("remapped" in warning for warning in report.warnings)

    # Stratified split should keep sparse types in train and test when enough PMIDs exist.
    split_types: dict[str, set[str]] = {"train": set(), "validation": set(), "test": set()}
    for split in split_types:
        path = tmp_path / "pack" / "annotation_splits" / f"ner_{split}.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for entity in row.get("entities") or []:
                split_types[split].add(str(entity.get("label")))
    assert "CELL_STATE" in split_types["train"]
    assert "CELL_STATE" in split_types["test"] or "TRIAL_PHASE" in split_types["test"]
    assert "PATHWAY" in split_types["train"]


def test_label_drift_uses_bio_label_map(tmp_path: Path) -> None:
    from gbmbert.training.governance import build_training_label_drift_report

    pack = tmp_path / "ner_bio_pack"
    splits = pack / "annotation_splits"
    maps = pack / "label_maps"
    splits.mkdir(parents=True)
    maps.mkdir(parents=True)
    row = {
        "task": "ner",
        "ner_encoding": "bio",
        "source_pmid": "1",
        "text": "glioblastoma",
        "label": "DISEASE",
        "entities": [{"text": "glioblastoma", "label": "DISEASE", "start": 0, "end": 12}],
    }
    for split in ("train", "validation", "test"):
        (splits / f"ner_{split}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    (maps / "ner_label_map.json").write_text(
        json.dumps(
            {
                "task": "ner",
                "encoding": "bio",
                "label_to_id": {"O": 0, "B-DISEASE": 1, "I-DISEASE": 2},
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "bio.json"
    config_path.write_text(
        json.dumps(
            {
                "name": "bio",
                "governance_profile": "scaffold",
                "governance_dataset_dir": str(splits).replace("\\", "/"),
                "task": "ner",
                "base_model": "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                "train_path": str(splits / "ner_train.jsonl").replace("\\", "/"),
                "validation_path": str(splits / "ner_validation.jsonl").replace("\\", "/"),
                "output_dir": str(tmp_path / "out").replace("\\", "/"),
                "label_set": ["O", "B-DISEASE", "I-DISEASE"],
                "hyperparameters": {"epochs": 1, "learning_rate": 2e-5, "batch_size": 2, "max_length": 64, "seed": 1},
                "training_enabled": False,
            }
        ),
        encoding="utf-8",
    )

    report = build_training_label_drift_report(config_paths=[config_path])

    assert report.warning_count == 0
    assert report.rows[0].dataset_labels["train"] == ["B-DISEASE", "I-DISEASE", "O"]
