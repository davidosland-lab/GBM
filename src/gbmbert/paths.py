"""Standard local artifact paths for the GBM-AI project."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = Path(".")
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    review_dir: Path = Path("data/review")
    training_dir: Path = Path("data/training")
    examples_dir: Path = Path("data/examples")
    query_packs_dir: Path = Path("data/query_packs")
    reports_dir: Path = Path("reports")
    corpus_reports_dir: Path = Path("reports/corpus")
    graph_reports_dir: Path = Path("reports/graph")
    review_reports_dir: Path = Path("reports/review")
    training_reports_dir: Path = Path("reports/training")
    wireframes_dir: Path = Path("reports/wireframes")
    docs_dir: Path = Path("docs")
    configs_dir: Path = Path("configs")
    models_dir: Path = Path("models")

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}

    def ensure_artifact_dirs(self) -> None:
        for path in [
            self.raw_dir,
            self.processed_dir,
            self.review_dir,
            self.training_dir,
            self.examples_dir,
            self.query_packs_dir,
            self.corpus_reports_dir,
            self.graph_reports_dir,
            self.review_reports_dir,
            self.training_reports_dir,
            self.models_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


DEFAULT_PATHS = ProjectPaths()


def standard_paths() -> ProjectPaths:
    """Return the local artifact path convention used by CLIs."""

    return DEFAULT_PATHS
