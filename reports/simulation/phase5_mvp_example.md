# Phase 5 Tumour Simulation Report (Research Prototype)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Pack: `compartment_toy_v1`
- Phase: Phase 5 research prototype
- Clinical validity claimed: `False`
- Resistance axis enabled: `False`

Phase 5 MVP: literature-parameterized Neftel-inspired four-compartment logistic growth toy model with baseline vs TMZ vs TMZ+FUS scenarios. Research prototype only - not a biophysical digital twin and not clinically validated.

## Boundary

### Simulated
- Discrete-time Neftel-inspired compartment abundances
- Logistic growth with shared carrying capacity
- Toy state transitions and kill/pressure scenario knobs
- Optional evidence-tier and relation-type research weighting from graph JSONL

### Not simulated
- Patient-specific clinical outcomes or imaging-constrained geometry
- Validated pharmacokinetics / pharmacodynamics
- Spatial invasion, vasculature, or full immune digital twin
- Clinical decision support or patient-ready treatment prescriptions
- Clinical validity or patient-ready predictions

## Assumptions
- Compartment labels follow a Neftel-inspired MES/NPC/OPC/AC vocabulary for research alignment only.
- Growth is discrete-time logistic with a shared carrying capacity.
- Transition rates are symmetric toy leakage, not inferred from single-cell data in this MVP.
- Kill and delivery multipliers are explicit scenario knobs with literature-themed anchors, not patient-ready predictions.
- Phase 6 may rank these toy scenarios for research comparison only; it is not CDS and not a prescription engine.
- KG-driven modulation uses relation-type research weights only (ENHANCES_DELIVERY_OF -> delivery scale, PREDICTS/IMPROVES -> kill scale, SYNERGIZES_WITH -> combo bonus, TRANSITIONS_TO -> transition scale).
- Modulation bounds are explicit toy clamps, not calibrated effect sizes.
- Resolved scales: evidence=0.950, delivery=1.147, kill=1.127, transition=1.000, synergy=1.000.

## Literature anchors (explicit, non-clinical)
- PMID `31327527`: Neftel et al. cell-state framework cited as vocabulary inspiration only (not used to fit rates here).
- PMID `29097493`: Sample graph fixture includes MGMT-to-TMZ response PREDICTS relation as an evidence-tier example.
- PMID `40000001`: Sample graph fixture includes FUS ENHANCES_DELIVERY_OF temozolomide as a delivery-modifier example.

## Graph research features
- Source: `data\examples\graph_records_sample.jsonl`
- Relations: 2
- Mean evidence tier: 2.0
- Evidence modulation: 0.95
- Delivery modulation: 1.147
- Kill modulation: 1.1265
- Synergy modulation: 1.0
- Transition modulation: 1.0
- Relation types: ENHANCES_DELIVERY_OF=1, PREDICTS=1

### Parameter provenance (research weights)
- `kill_modulation`=1.1265 (n=1, aggregation=mean_tier_confidence)
- `delivery_modulation`=1.147 (n=1, aggregation=mean_tier_confidence)
- `kill_modulation` via `PREDICTS` PMID `29097493` tier=3 weight=0.755
- `delivery_modulation` via `ENHANCES_DELIVERY_OF` PMID `40000001` tier=1 weight=0.42

## Scenario comparison table (toy totals)
| scenario | label | final_total | midpoint_total | delta_vs_baseline | relative_reduction |
| --- | --- | --- | --- | --- | --- |
| baseline | Baseline growth (no cytotoxic pressure) | 2.7735 | 1.8502 | 0.0000 | 0.0000 |
| tmz | Toy TMZ pressure | 1.0470 | 1.0243 | 1.7265 | 0.6225 |
| tmz_fus | Toy TMZ + FUS delivery multiplier | 0.4086 | 0.6136 | 2.3649 | 0.8527 |

## Final compartment states
- `baseline`: MES=0.7288, NPC=0.7100, OPC=0.6767, AC=0.6580, total=2.7735
- `tmz`: MES=0.3303, NPC=0.2438, OPC=0.2231, AC=0.2498, total=1.0470
- `tmz_fus`: MES=0.1497, NPC=0.0866, OPC=0.0757, AC=0.0966, total=0.4086

## Reminder

Phase 5 is a research prototype. Do not use these trajectories for diagnosis, treatment selection, or clinical decision-making. Scenario rankings from Phase 6 are research comparisons under toy assumptions, not prescriptions or CDS.
