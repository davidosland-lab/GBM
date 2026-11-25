# BIO NER v6 vs v3 (informative)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

**Not a freeze-split compare.** v6 trains on a cleaned BIO pack (UNKNOWN keyword dumps dropped, gene-symbol PATHWAY→GENE remaps, stratified sparse PMID split, sparse-doc oversample ×2, tempered class weights `power=0.5` / `max_ratio=20`, `max_steps=800`). v3 used the prior noisier pack.

| Run | Span accuracy | Type macro-F1 | Entity types |
|-----|---------------|---------------|--------------|
| v3 | 0.958 | 0.301 | 12 (incl. UNKNOWN) |
| **v6 (preferred)** | **0.987** | **0.691** | 11 (UNKNOWN dropped) |

## Sparse residual on v6 test

| Type | Support | F1 |
|------|---------|-----|
| CELL_STATE | 2 | 0.00 |
| PATHWAY | 1 | 0.00 |
| TRIAL_PHASE | 1 | 0.09 |

Major types (DISEASE/DRUG/GENE/OUTCOME/TREATMENT/…) recovered strong precision after weight tempering. Sparse-type F1 remains fragile on tiny test n.

## Research target

Proposed Phase 4 stretch Q4: type macro-F1 ≥ 0.40 with span ≥ 0.90 → **met** by v6 on the cleaned pack.
