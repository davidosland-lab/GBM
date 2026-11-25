# Phase 5 Monte Carlo Simulation Report (Research Prototype)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Config: `monte_carlo_v1`
- Phase: Phase 5 Monte Carlo research prototype
- Seed: `7`
- Samples: `40`
- Clinical validity claimed: `False`

Phase 5 Monte Carlo sweeps over toy growth parameters for baseline/TMZ/TMZ+FUS scenarios. Research prototype only — not clinical uncertainty quantification.

## Boundary

### Simulated
- Seedable Monte Carlo sweeps over toy growth parameters
- Per-scenario outcome distributions (final_total)
- Quantile / uncertainty-band summaries for research comparison

### Not simulated
- Clinical uncertainty quantification or validated posterior inference
- Patient-specific predictive intervals
- Treatment prescriptions or clinical decision support

## Assumptions
- Parameter distributions are explicit research priors, not fitted patient posteriors.
- Each draw reruns the deterministic toy scenario pack.
- Quantile bands summarize in-silico outcome spread only.
- Monte Carlo seed=7, n_samples=40 (research prototype).
- Parameter draws are independent toy distributions, not empirically fitted posteriors.
- Uncertainty bands are sample quantiles of in-silico outcomes only.

## Parameter distributions
- `intrinsic_growth_rate`: dist=normal, mean=0.08, std=0.015, low=0.02, high=0.16
- `carrying_capacity`: dist=uniform, mean=4.0, std=0.5, low=3.0, high=5.0
- `transition_rate`: dist=normal, mean=0.02, std=0.005, low=0.005, high=0.05

## Scenario uncertainty bands (toy final_total)
| scenario | label | median | q05 | q95 | mean | rel_reduction_vs_baseline |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | Baseline growth (no cytotoxic pressure) | 2.7244 | 2.2424 | 3.1409 | 2.7326 | 0.0000 |
| tmz | Toy TMZ pressure | 1.2799 | 0.8872 | 1.5515 | 1.2613 | 0.5302 |
| tmz_fus | Toy TMZ + FUS delivery multiplier | 0.6299 | 0.3942 | 0.7668 | 0.6090 | 0.7688 |

## Reminder

Monte Carlo bands are research quantiles over toy parameter draws. They are not clinical prediction intervals and must not be used for diagnosis, treatment selection, or clinical decision-making.
