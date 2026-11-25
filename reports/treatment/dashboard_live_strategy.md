# Phase 6 Treatment Scenario Ranking (Research Prototype)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Research-use only. Not medical advice. Not clinical decision support (CDS). Not intended for diagnosis, treatment selection, dosing, or clinical decision-making. Scenario ranks are toy in-silico comparisons, not prescriptions. No patient eligibility screening. Intensity/schedule knobs are simulation parameters only.

- Config: `strategy_research_v1`
- Simulation pack: `compartment_toy_v1`
- Phase: Phase 6 treatment strategy research prototype
- Clinical validity claimed: `False`
- Clinical decision support: `False`

Phase 6 research prototype: rank Phase 5 toy simulation scenarios (baseline/TMZ/TMZ+FUS) under explicit multi-criteria research weights including toy efficacy vs toy toxicity/burden trade-offs. Optional intensity/schedule knobs are simulation parameters only. Not CDS. Not medical advice. Not clinically validated. No patient eligibility.

## Boundary

### Compared (research)
- Ranking of Phase 5 simulation scenarios under toy multi-criteria weights
- Optional graph evidence-support term as a research score component
- Toy efficacy vs toy toxicity/burden trade-off scores (research only)
- Optional intensity_scale / schedule_duty_cycle simulation-parameter knobs
- Transparent comparison tables and ranking provenance for in-silico exploration

### Not provided
- Real-patient treatment selection, dosing, or scheduling
- Clinical decision support or prescription generation
- Validated efficacy/toxicity trade-off optimization
- Patient eligibility screening or real-world inclusion criteria
- Regulatory or bedside recommendations

## Assumptions
- Scenarios are Phase 5 toy knobs (kill rate / delivery multiplier), not real dosing schedules.
- Ranking maximizes a transparent research score; it does not optimize clinical utility.
- Toy toxicity/burden is a synthetic research score, not clinical AE prediction.
- intensity_scale and schedule_duty_cycle scale simulation kill pressure only — not real regimens.
- Evidence-support terms from graph JSONL are research weights only.
- No patient eligibility screening or clinical decision support.
- Outputs must never be interpreted as prescriptions or clinical recommendations.
- Ranks compare Phase 5 toy simulation scenarios only.
- Scores use explicit transparent weights; they are not clinically optimized.
- Toy toxicity/burden is a synthetic research score — not clinical toxicity or AE prediction.
- Intensity/schedule knobs scale simulation kill pressure only — not real dosing schedules.
- No patient eligibility, CDS, or prescription generation.
- Higher research_score means better in-silico scenario under the configured toy objective - not a treatment recommendation.
- Research-use only. Not medical advice. Not clinical decision support (CDS). Not intended for diagnosis, treatment selection, dosing, or clinical decision-making. Scenario ranks are toy in-silico comparisons, not prescriptions. No patient eligibility screening. Intensity/schedule knobs are simulation parameters only.

## Ranking weights (toy)
- `relative_reduction`: 0.45
- `final_burden_inverse`: 0.2
- `delivery_efficiency`: 0.1
- `evidence_support`: 0.1
- `toxicity_inverse`: 0.15

## Scenario research knobs (simulation parameters only — not real schedules)
- `intensity_scale`: 1.0
- `schedule_duty_cycle`: 1.0

## Ranking provenance
- Method: `transparent_weighted_sum_over_normalized_toy_components`
- Toxicity model: `toy_kill_x_delivery_x_intensity_x_duty_proxy`
- Patient eligibility: `False` (must remain false)
- Higher research_score means better under the configured toy objective only.
- toxicity_inverse rewards lower toy_toxicity_burden (research score, not clinical AEs).
- intensity_scale and schedule_duty_cycle are simulation knobs, not prescriptions.

## Literature anchors (explicit, non-clinical)
- PMID `29097493`: Sample PREDICTS relation used only as an optional evidence-support signal.
- PMID `40000001`: Sample FUS ENHANCES_DELIVERY_OF relation used only as delivery-theme context.

## Optional graph evidence signals
- Relations: 2
- Mean evidence tier: 2.0
- Evidence modulation: 0.95

## Scenario ranking table (research scores only)
| rank | scenario | label | research_score | relative_reduction | final_total | toy_toxicity | delivery_multiplier | intensity | duty_cycle |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | tmz_fus | Toy TMZ + FUS delivery multiplier | 0.8500 | 0.8527 | 0.4086 | 0.1163 | 2.0646 | 1.0000 | 1.0000 |
| 2 | tmz | Toy TMZ pressure | 0.2500 | 0.6225 | 1.0470 | 0.0646 | 1.1470 | 1.0000 | 1.0000 |

## Reminder

These ranks compare toy simulation scenarios. They are not prescriptions, not dosing advice, and not clinical decision support. Toy toxicity scores are synthetic research burdens, not clinical adverse-event models. Intensity/schedule knobs are simulation parameters only. Do not use for diagnosis, treatment selection, patient eligibility, or clinical decision-making.
