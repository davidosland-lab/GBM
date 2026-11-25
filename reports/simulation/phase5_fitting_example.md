# Phase 5 Toy Parameter Fitting (Research Stub)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Research stub only. Not PK/PD. Not clinically validated posteriors. Toy-target acceptance sampling for in-silico exploration — not patient-ready inference.

- Config: `toy_fitting_v1`
- Phase: Phase 5 toy parameter-fitting research stub
- Clinical validity claimed: `False`
- Is PK/PD: `False` (must remain false)
- Seed: `17`
- Draws / accepted / kept: `80` / `80` / `12`
- Relative tolerance: `0.35`

Phase 5 research stub: approximate posterior-style sampling against toy scenario final_total targets. Not PK/PD. Not clinically calibrated posteriors. Not a digital twin.

## Boundary

### Simulated (research)
- Rejection / approximate posterior-style sampling against toy scenario targets
- Optional soft graph-derived constraint term (research weight only)
- Particle summaries (mean/std of accepted draws) for research exploration

### Not simulated / out of scope
- Pharmacokinetics / pharmacodynamics (explicitly out of scope)
- Spatially resolved biophysics or imaging-constrained geometry
- Empirically calibrated clinical posteriors or patient-ready inference
- Clinical decision support or treatment prescriptions

## Assumptions
- Targets are synthetic research set-points for the offline fixture pack, not clinical observations.
- Accepted particles are toy approximate-posterior samples only.
- Explicitly not pharmacokinetics/pharmacodynamics and not spatial biophysics.
- Research stub only. Not PK/PD. Not clinically validated posteriors. Toy-target acceptance sampling for in-silico exploration — not patient-ready inference.
- Toy targets: {'baseline': 1.15, 'tmz': 1.05, 'tmz_fus': 0.95}
- Acceptance relative_tolerance=0.35; seed=17.
- Accepted particles are research samples, not validated clinical posteriors.
- This module is explicitly not PK/PD and not spatially resolved biophysics.

## Toy targets (scenario_id -> final_total)
- `baseline`: 1.15
- `tmz`: 1.05
- `tmz_fus`: 0.95

## Approximate posterior-style summary (accepted/kept particles)
| parameter | mean | std | min | max | n |
| --- | --- | --- | --- | --- | --- |
| intrinsic_growth_rate | 0.0896 | 0.0062 | 0.0818 | 0.1030 | 12 |
| carrying_capacity | 3.3610 | 0.5681 | 2.5210 | 4.4591 | 12 |
| transition_rate | 0.0220 | 0.0123 | 0.0058 | 0.0412 | 12 |

## Best particle (lowest toy score)
- Score: `0.188048`
- Overrides: `{'intrinsic_growth_rate': 0.10304199954777626, 'carrying_capacity': 2.5210176612816237, 'transition_rate': 0.023248837486520898}`
- Predictions: `{'baseline': 1.511997, 'tmz': 1.02969, 'tmz_fus': 0.738606}`

## Reminder

These particles approximate a research posterior against toy targets only. They are not PK/PD, not clinical posteriors, and not for diagnosis or treatment selection.
