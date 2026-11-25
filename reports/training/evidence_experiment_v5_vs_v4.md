# Evidence Experiment v5 vs v4 (Stabilize Tiers 0/2/4)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Headline
- v4 accuracy / macro-F1: 0.404 / 0.258
- v5 accuracy / macro-F1: 0.531 / 0.467
- Delta accuracy / macro-F1: +0.128 / +0.209

## Round 20 data change
- 70 abstracts biased to review/hypothesis, animal, phase I/II -> 68 evidence (13 tier 0, 27 tier 2, 14 tier 4) + 2 relations
- Pack after rebuild: 633 evidence / 7081 NER / 217 relation (promotable)
- Test label counts now: {'0': 11, '1': 6, '2': 6, '3': 32, '4': 2, '5': 7}

## Per-label F1 / recall
- 0: F1 0.0 -> 0.3846153846153846; recall 0.0 -> 0.45454545454545453 (support 11)
- 1: F1 0.56 -> 0.4705882352941177; recall 0.7777777777777778 -> 0.6666666666666666 (support 6)
- 2: F1 0.0 -> 0.8333333333333334; recall 0.0 -> 0.8333333333333334 (support 6)
- 3: F1 0.5454545454545454 -> 0.6153846153846154; recall 0.5 -> 0.5 (support 32)
- 4: F1 0.0 -> 0.0; recall 0.0 -> 0.0 (support 2)
- 5: F1 0.4444444444444445 -> 0.5; recall 1.0 -> 0.5714285714285714 (support 7)

## Note
- Research artifact only; not clinical validation. Test split changed after Round 20 rebuild, so deltas are directional.
