from gbmbert.paths import standard_paths


def test_standard_paths_expose_artifact_conventions() -> None:
    paths = standard_paths()

    assert str(paths.raw_dir) == "data\\raw" or str(paths.raw_dir) == "data/raw"
    assert paths.to_dict()["processed_dir"].replace("\\", "/") == "data/processed"
    assert paths.to_dict()["training_dir"].replace("\\", "/") == "data/training"
    assert paths.to_dict()["graph_reports_dir"].replace("\\", "/") == "reports/graph"
    assert paths.to_dict()["models_dir"] == "models"
