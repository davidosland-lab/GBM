# Evidence Experiment v3 vs v2 (Quality Pass)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Headline
- v2 accuracy / macro-F1: 0.600 / 0.152
- v3 accuracy / macro-F1: 0.440 / 0.301
- Delta accuracy / macro-F1: -0.160 / +0.149

## Changes in v3
- Inverse-frequency class-weighted cross-entropy (use_class_weights: true)
- 3 epochs (was 1)
- Fixed seed 13

## Per-label F1 / recall
- 0: F1 0.16666666666666669 -> 0.3846153846153846; recall 0.09090909090909091 -> 0.45454545454545453 (support 11)
- 1: F1 0.0 -> 0.0; recall 0.0 -> 0.0 (support 0)
- 2: F1 0.0 -> 0.5; recall 0.0 -> 0.42857142857142855 (support 7)
- 3: F1 0.7435897435897436 -> 0.52; recall 1.0 -> 0.4482758620689655 (support 29)
- 4: F1 0.0 -> 0.4; recall 0.0 -> 1.0 (support 1)
- 5: F1 0.0 -> 0.0; recall 0.0 -> 0.0 (support 2)

## Corpus prediction mix (912 claims)
- v2: {'3': 912}
- v3: {'0': 327, '1': 91, '2': 67, '3': 345, '4': 60, '5': 22}

## Note
- Research artifact only; not clinical validation.
