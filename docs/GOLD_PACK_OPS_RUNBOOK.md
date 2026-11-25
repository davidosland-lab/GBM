# Gold Pack Ops Runbook

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

## Differentiation bet

Invest in the **gold-pack / curation / governance** asset (evidence tiers, dual-review, active learning, promotion gates, provenance) rather than competing on lit-mining scale or clinical ranking / CDS.

Promotable ≠ clinically validated GBM-BERT. Preferred research checkpoints (as of Phase 4 DoD): evidence **v9**, relation **v3**, BIO NER **v6**.

## Weekly / next-round loop

```text
1. Status     → gbmbert-gold-pack-ops-status
2. Sample     → prep review batch / sparse densify dual-review / AL export
3. Review     → human accept|correct|reject (dual-review when quality-critical)
4. Adjudicate → gbmbert-adjudication-report (r1 vs r2)
5. Promote    → finalize / curated_expansion fixtures (no pending rows)
6. Rebuild    → gbmbert-rebuild-curated-rounds
7. Gates      → gbmbert-review-gold-pack-promotion + ops status
8. Metrics    → soft densify gaps, backlog, preferred-checkpoint note
9. Retrain?   → only when freeze-split compare is planned (document; do not casual-train)
```

### PowerShell (project root, `.venv`, `PYTHONPATH=src`)

```powershell
$env:PYTHONPATH = "src"

# 1) Pack health in one report
.\.venv\Scripts\gbmbert-gold-pack-ops-status.exe `
  --markdown-output reports\training\gold_pack\gold_pack_ops_status.md `
  --json-output reports\training\gold_pack\gold_pack_ops_status.json

# 2a) Sparse NER densify dual-review skeleton (pending; no invented labels)
.\.venv\Scripts\gbmbert-export-sparse-densify-batch.exe --round 33

# 2b) Or real PubMed review batch prep (evidence/relations; lexicon spans need 16BV)
.\.venv\Scripts\gbmbert-prep-review-batch.exe --round N --pubmed-jsonl data\research\roundN_pubmed.jsonl --reviewer YOU

# 3–4) Humans adjudicate queues under data\research\review_batches\roundN\
.\.venv\Scripts\gbmbert-adjudication-report.exe path\to\r1.jsonl path\to\r2.jsonl `
  --markdown-output reports\review\adjudication_roundN.md `
  --json-output reports\review\adjudication_roundN.json

# 5–6) Promote + rebuild
.\.venv\Scripts\gbmbert-finalize-review-batch.exe --round N
.\.venv\Scripts\gbmbert-rebuild-curated-rounds.exe

# 7) Re-check floors + ops
.\.venv\Scripts\gbmbert-review-gold-pack-promotion.exe --allow-blockers
.\.venv\Scripts\gbmbert-gold-pack-ops-status.exe
```

Launcher shortcuts: `16BM` promotion review, `16BO` promotion plan, `16BS` rebuild, `16BT`/`16BU` prep/finalize, `16BV`/`16BW` entity-span export/apply, `16CC` ops status.

Dashboard: Training Artifacts page shows promotion blockers, soft densify gaps, and next actions from the ops status report (research live runner; no GPU train).

## What “healthy” means

| Signal | Meaning |
| --- | --- |
| Hard promotion floors | `configs/training/gold_pack_promotion_thresholds.json` (task/label/PMID minima). Blocking when unmet. |
| Soft densify gaps | Ops-only quality targets above hard floors (sparse NER / thin relation / minority evidence tiers). Non-blocking. |
| Dual-review backlog | Pending span / reviewed-queue rows under `data/research/review_batches/`. |
| AL backlog | Pending active-learning batch rows. |
| Preferred checkpoints | Keep until a controlled freeze-split experiment says otherwise. |

## Explicit non-goals (leave alone)

- Clinical CDS / patient ranking / dosing
- Multi-hour GPU trains without a freeze-split plan
- Scaling PubMed harvest as the primary differentiation bet
- Inventing dual-review labels in automation

## Related CLIs

- `gbmbert-gold-pack-ops-status` — single health report
- `gbmbert-export-sparse-densify-batch` — pending sparse NER dual-review skeleton
- `gbmbert-review-gold-pack-promotion` / `gbmbert-plan-gold-pack-promotion`
- `gbmbert-export-active-learning-candidates` / `gbmbert-plan-active-learning-batches` / batch status CSV roundtrip
- `gbmbert-export-entity-span-review` / `gbmbert-apply-entity-span-review`
- `gbmbert-adjudication-report`
- `gbmbert-rebuild-curated-rounds`
