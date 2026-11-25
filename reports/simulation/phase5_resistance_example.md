# Phase 5 Tumour Simulation Report (Research Prototype)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Pack: `compartment_resistance_v1`
- Phase: Phase 5 research prototype
- Clinical validity claimed: `False`
- Resistance axis enabled: `True`

Phase 5 post-MVP: Neftel-inspired compartments plus optional sensitive/persister/resistant axis. Research prototype only — not clinically validated.

## Boundary

### Simulated
- Discrete-time Neftel-inspired compartment abundances
- Logistic growth with shared carrying capacity
- Toy state transitions and kill/pressure scenario knobs
- Optional evidence-tier and relation-type research weighting from graph JSONL
- Optional resistance-axis subpopulations (sensitive/persister/resistant)

### Not simulated
- Patient-specific clinical outcomes or imaging-constrained geometry
- Validated pharmacokinetics / pharmacodynamics
- Spatial invasion, vasculature, or full immune digital twin
- Clinical decision support or patient-ready treatment prescriptions
- Clinical validity or patient-ready predictions

## Assumptions
- Compartment labels follow a Neftel-inspired MES/NPC/OPC/AC vocabulary for research alignment only.
- Growth is discrete-time logistic with a shared carrying capacity.
- Resistance subpopulations are optional and explicitly toy-parameterized.
- Outputs are for in-silico hypothesis exploration only.

## Literature anchors (explicit, non-clinical)
- PMID `31327527`: Neftel et al. cell-state framework cited as vocabulary inspiration only.

## Scenario comparison table (toy totals)
| scenario | label | final_total | midpoint_total | delta_vs_baseline | relative_reduction |
| --- | --- | --- | --- | --- | --- |
| baseline | Baseline growth (no cytotoxic pressure) | 2.7735 | 1.8502 | 0.0000 | 0.0000 |
| tmz | Toy TMZ pressure | 1.4611 | 1.2221 | 1.3124 | 0.4732 |
| tmz_fus | Toy TMZ + FUS delivery multiplier | 0.8785 | 0.8760 | 1.8950 | 0.6833 |

## Final compartment states
- `baseline`: MES=0.7288, NPC=0.7100, OPC=0.6767, AC=0.6580, total=2.7735
  - resistance: sensitive=2.3575, persister=0.3328, resistant=0.0832
- `tmz`: MES=0.4347, NPC=0.3515, OPC=0.3262, AC=0.3487, total=1.4611
  - resistance: sensitive=1.0234, persister=0.3344, resistant=0.1034
- `tmz_fus`: MES=0.2845, NPC=0.2016, OPC=0.1826, AC=0.2097, total=0.8785
  - resistance: sensitive=0.4717, persister=0.2942, resistant=0.1126

## Reminder

Phase 5 is a research prototype. Do not use these trajectories for diagnosis, treatment selection, or clinical decision-making. Scenario rankings from Phase 6 are research comparisons under toy assumptions, not prescriptions or CDS.
