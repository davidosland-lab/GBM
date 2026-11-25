"""Phase 5 research prototype tumour simulation (toy compartment model).

Research-use only. Not medical advice. Not intended for diagnosis,
treatment selection, or clinical decision-making.

This package is an offline research prototype. It does not claim clinical
validity, patient-ready predictions, or biophysical digital-twin fidelity.
"""

from gbmbert.simulation.fitting import FittingReport, run_toy_parameter_fit
from gbmbert.simulation.model import CompartmentState, SimulationResult, step_simulation
from gbmbert.simulation.monte_carlo import MonteCarloReport, run_monte_carlo
from gbmbert.simulation.scenarios import ScenarioPack, run_scenario_pack

__all__ = [
    "CompartmentState",
    "FittingReport",
    "MonteCarloReport",
    "ScenarioPack",
    "SimulationResult",
    "run_monte_carlo",
    "run_scenario_pack",
    "run_toy_parameter_fit",
    "step_simulation",
]
