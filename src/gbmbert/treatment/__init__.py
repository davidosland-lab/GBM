"""Phase 6 research prototype treatment-scenario comparison engine.

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

This package ranks or compares *simulation scenarios* under explicit toy
assumptions. It is not clinical decision support, not a prescription engine,
and does not claim clinical validation.
"""

from gbmbert.treatment.engine import TreatmentStrategyReport, rank_treatment_scenarios

__all__ = [
    "TreatmentStrategyReport",
    "rank_treatment_scenarios",
]
