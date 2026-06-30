"""Biomedical entity extraction utilities."""

from gbmbert.extraction.entities import ExtractedEntity, EntityExtractionResult
from gbmbert.extraction.normalize import normalize_text

__all__ = [
    "BiomedicalNERPipeline",
    "EntityExtractionResult",
    "ExtractedEntity",
    "normalize_text",
]


def __getattr__(name: str) -> object:
    if name == "BiomedicalNERPipeline":
        from gbmbert.extraction.pipeline import BiomedicalNERPipeline

        return BiomedicalNERPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
