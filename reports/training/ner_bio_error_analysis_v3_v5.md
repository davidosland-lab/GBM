# BIO NER Error Analysis (v3 vs v5)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

Sources: `ner_bio_experiment_v3_metrics.json`, `ner_bio_experiment_v5_metrics.json`, current `ner_bio_pack`.

## Headline

| Run | Span accuracy | Type macro-F1 | Test gold spans |
|-----|---------------|---------------|-----------------|
| v3 (preferred) | 0.958 | 0.301 | 575 |
| v5 | 0.901 | 0.258 | 588 |

v5 trained after Round 29 densify on a **reshuffled** test (seed=13 rebuild). Compare is informative only.

## Sparse-type confusion (exact-span)

### CELL_STATE

- v3: support 4, recall 0.25, precision 0.0125 → F1 0.024; **79 FP** predictions
- v5: support 5, recall 0.80, precision 0.020 → F1 0.038; **199 FP** predictions
- Mentions look plausible (`mesenchymal`, `invasive`, `stem-like`, `hypoxic`) but class-weighted BIO over-predicts the type.

### PATHWAY

- v3: support 2, recall 1.0, precision 0.014 → F1 0.027; **143 FP**
- v5: support 9, recall 0.0, precision 0.0 → F1 0.0; **33 FP**
- Gold noise: **~30/53** PATHWAY spans are single-token gene symbols (`EGFR`×18, `PI3K`×9, `AKT`, `PD-L1`) that should be GENE. True pathways (`PI3K/AKT`, `MAPK pathway`, `NF-κB`) are a minority.

### TRIAL_PHASE

- v3: support 2, F1 0.071 (1 TP / 1 FN; 25 FP)
- v5: support 7, F1 0.081 (4 TP / 3 FN; 88 FP)

### UNKNOWN

- v3: support 3, F1 0.0 (never predicted correctly)
- v5: support 7, F1 0.068
- Gold noise: nearly all UNKNOWN mentions are discourse/hedge keywords (`elusive`, `putative`, `However`, `Furthermore`, `poorly characterized`, …) — not entities.

## Dominant failure mode

High **recall + low precision** on many types, driven by:

1. Inverse-frequency class weights on token BIO tags over-upweight rare `B-/I-` tags → mass false-positive spans (`__MISS__` → type).
2. Label noise in PATHWAY (gene symbols) and UNKNOWN (keyword dumps).
3. Tiny test support for sparse types makes type macro-F1 unstable across rebuilds.

Major types (DISEASE/DRUG) keep solid F1 (~0.6–0.7 on v3) despite FP burden; sparse types drag macro-F1 to ~0.30.

## Levers for v6+

1. Drop UNKNOWN from BIO training pack (keyword-dump cleanup).
2. Remap gene-symbol PATHWAY → GENE at pack build.
3. Stratified PMID split preserving sparse types in train+test.
4. Oversample sparse-type train docs.
5. Temper class weights (`class_weight_power=0.5`, `class_weight_max_ratio≈20`) + longer `max_steps`.
6. Keep v3 as baseline until a run beats span ≥ 0.90 **and** type macro-F1 ≥ 0.40 (or documents a residual block).
