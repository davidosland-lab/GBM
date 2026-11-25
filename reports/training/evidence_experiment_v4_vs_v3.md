# Evidence Experiment v4 vs v3 (Minority-Tier Refill)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Headline
- v3 accuracy / macro-F1: 0.440 / 0.301
- v4 accuracy / macro-F1: 0.404 / 0.258
- Delta accuracy / macro-F1: -0.036 / -0.042

## Round 19 data change
- 70 minority-cue abstracts -> 67 accepted evidence (48 tier 1, 12 tier 5) + 4 relations
- Test label counts now: {'0': 12, '1': 9, '2': 4, '3': 24, '4': 4, '5': 4}

## Per-label F1 / recall
- 0: F1 0.3846153846153846 -> 0.0; recall 0.45454545454545453 -> 0.0 (support 12)
- 1: F1 0.0 -> 0.56; recall 0.0 -> 0.7777777777777778 (support 9)
- 2: F1 0.5 -> 0.0; recall 0.42857142857142855 -> 0.0 (support 4)
- 3: F1 0.52 -> 0.5454545454545454; recall 0.4482758620689655 -> 0.5 (support 24)
- 4: F1 0.4 -> 0.0; recall 1.0 -> 0.0 (support 4)
- 5: F1 0.0 -> 0.4444444444444445; recall 0.0 -> 1.0 (support 4)

## Corpus prediction mix
- v4: {'0': 169, '1': 236, '2': 27, '3': 295, '4': 34, '5': 151}

## Note
- Research artifact only; not clinical validation.
