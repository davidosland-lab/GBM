# Relation Experiment v2 vs v1 (IMPROVES/WORSENS Fill)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Headline
- v1 accuracy / macro-F1: 0.560 / 0.437
- v2 accuracy / macro-F1: 0.625 / 0.577
- Delta accuracy / macro-F1: +0.065 / +0.141

## Round 22 data change
- Mined 40 accepted IMPROVES/WORSENS sentence relations from gold entities + abstracts
- Relation pack train IMPROVES/WORSENS roughly doubled vs pre-fill

## Per-label F1 / recall
- ASSOCIATED_WITH: F1 0.5263157894736842 -> 0.8; recall 0.625 -> 0.6666666666666666 (support 12)
- IMPROVES: F1 0.0 -> 0.5; recall 0.0 -> 1.0 (support 3)
- NO_RELATION: F1 0.8235294117647058 -> 0.8; recall 0.7 -> 1.0 (support 2)
- PREDICTS: F1 0.5 -> 0.5; recall 0.3333333333333333 -> 1.0 (support 1)
- WORSENS: F1 0.3333333333333333 -> 0.2857142857142857; recall 0.5 -> 0.16666666666666666 (support 6)

## Note
- Research artifact only; not clinical validation.
