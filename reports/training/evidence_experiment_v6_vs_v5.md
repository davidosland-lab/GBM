# Evidence Experiment v6 vs v5 (Tier-4 Refill)

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Headline
- v5 accuracy / macro-F1: 0.531 / 0.467
- v6 accuracy / macro-F1: 0.479 / 0.453
- Delta accuracy / macro-F1: -0.052 / -0.015

## Round 21 data change
- Fetched phase I/II PubMed pack + relation-biased abstracts → 76 evidence (33 tier 4) + 2 relations
- Pack after Round 21/22 rebuild: 709 evidence / 7653 NER / 259 relation (promotable)
- Test label counts now: {'0': 9, '1': 13, '2': 3, '3': 31, '4': 9, '5': 6}

## Per-label F1 / recall
- 0: F1 0.3846153846153846 -> 0.34782608695652173; recall 0.45454545454545453 -> 0.4444444444444444 (support 9)
- 1: F1 0.4705882352941177 -> 0.4761904761904762; recall 0.6666666666666666 -> 0.38461538461538464 (support 13)
- 2: F1 0.8333333333333334 -> 0.28571428571428575; recall 0.8333333333333334 -> 0.6666666666666666 (support 3)
- 3: F1 0.6153846153846154 -> 0.5200000000000001; recall 0.5 -> 0.41935483870967744 (support 31)
- 4: F1 0.0 -> 0.7999999999999999; recall 0.0 -> 0.8888888888888888 (support 9)
- 5: F1 0.5 -> 0.28571428571428575; recall 0.5714285714285714 -> 0.3333333333333333 (support 6)

## Note
- Research artifact only; test split changed after rebuild, so deltas are directional.
