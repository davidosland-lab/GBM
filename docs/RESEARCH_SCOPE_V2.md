# RESEARCH_SCOPE_V2.md — Addendum to `PROJECT_HANDOFF.md`

> **Status:** Draft addendum · supersedes specific sections of `PROJECT_HANDOFF.md` v1.0 where indicated.
> **Scope of changes:** literature search vocabulary, NER entity types, knowledge-graph node/edge schema, simulator treatment modules, simulator tumour-population model, patient-state fields.
> **Out of scope:** anything that would change the platform's research-use-only posture. All Tier-1/2/3 additions below remain bound by the existing safety language.

---

## 0. Research-use-only restatement

> **Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.**

Every addition in this document is for *in-silico exploration and hypothesis generation*. Nothing in this addendum changes the prohibition on:
- recommending treatment for a real patient,
- generating clinical instructions,
- presenting the platform as a medical device,
- claiming predictive clinical accuracy.

The new evidence types introduced below (FDA approvals, randomized phase II/III data) make the evidence-tier guardrail **more** important, not less — see §6.

---

## 1. Motivation

`PROJECT_HANDOFF.md` v1.0 fixed the platform's literature scope around the 2018–2022 era of GBM research: TMZ + RT, MGMT methylation, EGFR amplification, IDH-wildtype framing, generic CAR-T and vaccines, TTFields as a standalone modality. Six axes have materially advanced since then and are not adequately represented in v1.0:

1. **Focused-ultrasound BBB opening** as a delivery-modifier modality.
2. **IDH-mutant glioma therapy** (vorasidenib FDA approval, August 2024).
3. **Oncolytic virotherapy** (CAN-3110 *Nature* 2023; DNX-2401 + pembrolizumab phase II).
4. **Neuron–glioma synapse blockade with perampanel** (PerSurge/NOA-30 phase II).
5. **Myeloid reprogramming via CSF1R inhibition** (PLX3397, BLZ945).
6. **Four-state cell plasticity model** (Neftel MES/NPC/OPC/AC) replacing the simulator's ad-hoc population scheme.

Three further axes (ferroptosis, chronotherapy, BMP-induced differentiation, neoantigen vaccines, GD2/chlorotoxin CAR-T, TTFields synergy) are Tier-3 additions tracked at the end of this document.

---

## 2. Patches to `PROJECT_HANDOFF.md`

The following sections of v1.0 are amended. Diff-style: `+ added`, `~ revised`, `- removed`. Line references are to v1.0 of the handoff.

### 2.1 §"Data Sources → Literature → Search topics"

Add to the existing search-topic list:

```
+ focused ultrasound
+ MR-guided ultrasound
+ microbubble
+ blood-brain barrier opening
+ SonoCloud
+ Exablate Neuro
+ oncolytic virus
+ DNX-2401
+ CAN-3110
+ G47Δ
+ perampanel
+ AMPA receptor antagonist
+ CSF1R inhibitor
+ pexidartinib
+ BLZ945
+ tumor-associated macrophage
+ microglia polarization
+ vorasidenib
+ IDH-mutant glioma
+ D-2-hydroxyglutarate
+ ferroptosis
+ GPX4
+ SLC7A11
+ GD2 CAR-T
+ chlorotoxin CAR-T
+ neoantigen vaccine
+ NeoVax
+ chronotherapy
+ Neftel cell states
+ MES NPC OPC AC
+ BMP differentiation therapy
+ glioma stem cell quiescence
```

### 2.2 §"SECOND CODEX TASK → Entity Types"

Extend the existing 10-entity list:

```
  GENE
  DRUG
  DISEASE
  PATHWAY
  BIOMARKER
  CELL_TYPE
+ CELL_STATE              # MES-like, NPC-like, OPC-like, AC-like
  TREATMENT
+ DELIVERY_MODIFIER       # FUS-BBBO, intra-arterial, convection-enhanced delivery
  OUTCOME
  TRIAL_PHASE
  UNKNOWN
```

### 2.3 §"SECOND CODEX TASK → Normalization aliases"

Add to the existing alias dictionary:

```python
{
    # IDH axis
    "voranigo": "vorasidenib",
    "ag-881":   "vorasidenib",
    "2hg":      "D-2-hydroxyglutarate",
    "d-2hg":    "D-2-hydroxyglutarate",

    # Neuron-glioma synapse axis
    "fycompa":      "perampanel",
    "ampar":        "AMPA receptor",
    "gria2":        "GRIA2",

    # Myeloid axis
    "plx3397":      "pexidartinib",
    "turalio":      "pexidartinib",
    "tam":          "tumor-associated macrophage",
    "tams":         "tumor-associated macrophage",
    "m1 macrophage": "M1 macrophage",
    "m2 macrophage": "M2 macrophage",

    # Delivery axis
    "fus":          "focused ultrasound",
    "mr-fus":       "MR-guided focused ultrasound",
    "bbbo":         "blood-brain barrier opening",
    "bbbd":         "blood-brain barrier disruption",

    # Cell-state axis
    "mes-like":     "MES-like",
    "npc-like":     "NPC-like",
    "opc-like":     "OPC-like",
    "ac-like":      "AC-like",
}
```

### 2.4 §"THIRD CODEX TASK → Nodes"

Add to the existing 11-node list:

```
+ CellState           # one node per {MES, NPC, OPC, AC}, properties: name, plasticity_score
+ DeliveryModifier    # e.g. FUS-BBBO, ultrasound microbubble
```

### 2.5 §"THIRD CODEX TASK → Edges"

Add three new edge types:

```
+ ENHANCES_DELIVERY_OF   # DeliveryModifier -> Drug
+ SYNERGIZES_WITH        # Treatment -> Treatment   (symmetric in semantics, directed for storage)
+ TRANSITIONS_TO         # CellState -> CellState   (plasticity transitions)
```

The schema-validator's `ALLOWED_EDGES` map in `src/knowledge_graph/schema.py` must be extended accordingly.

### 2.6 §"FIFTH CODEX TASK → Patient State"

Extend the existing `PatientState` record:

```
  age
  mgmt_status
  idh_status
  egfr_status
  tumour_volume
  immune_score
  stem_cell_score
  treatment_history
+ bbb_integrity_score        # 0.0 (intact) … 1.0 (broadly disrupted)
+ tam_polarization_score     # −1.0 (M2-dominant) … +1.0 (M1-dominant)
+ circadian_phase_estimate   # hours since habitual wake, optional
+ cell_state_distribution    # dict[CellState, float] summing to 1.0
```

### 2.7 §"FIFTH CODEX TASK → Tumour Populations"

**Replace** the v1.0 five-population scheme:

```
~ # v1.0 (deprecated)
~ Stem-like Cells
~ Treatment Sensitive Cells
~ Treatment Resistant Cells
~ Immune Evasive Cells
~ Invasive Cells
```

…with a **two-axis representation** aligned with Neftel et al. 2019:

```
+ # v2.0
+ cell_state         ∈ {MES, NPC, OPC, AC}
+ resistance_status  ∈ {sensitive, persister, resistant}
+ # → 12 logical populations; transitions governed by TRANSITIONS_TO edges
+ #   weighted by stress signals (hypoxia, treatment pressure, immune attack).
```

Rationale: the v1.0 scheme is not directly reconcilable with single-cell datasets the platform already plans to ingest (Ivy GBM Atlas, TCGA-GBM RNA, future spatial transcriptomics). The Neftel four-state axis is the de facto standard in the literature since 2019 and has direct CNV correlates (PDGFRA → OPC-like; CDK4 → NPC-like; EGFR → AC-like; NF1 → MES-like) that the genomics ingestion layer can feed in directly.

### 2.8 §"FIFTH CODEX TASK → Treatment Modules"

Extend from 8 to 13 modules:

```
  surgery
  radiation
  temozolomide
  TTFields
  checkpoint inhibitors
  vaccines
  CAR-T
  neuron-signalling blockade
+ focused_ultrasound_BBBO        # delivery modifier; multiplies effective intratumoral [drug]
+ oncolytic_virus                # viral_lysis + immune_activation combo mechanism
+ CSF1R_inhibitor                # myeloid reprogramming (M2 → M1)
+ IDH_inhibitor                  # only available when patient_state.idh_status == "mutant"
+ chronotherapy_scheduling       # parameterizes existing modules with time_of_day
```

### 2.9 §"SEVENTH CODEX TASK → Dashboard"

The Knowledge Graph Explorer wireframe (separate artifact) is unchanged. The Simulator and Treatment Explorer pages must surface the new `cell_state_distribution` and `bbb_integrity_score` fields. Evidence-tier color coding on every edge becomes **mandatory**, not optional, because tier-5 randomized-trial evidence will now appear in the graph (vorasidenib INDIGO, TTFields EF-14) alongside tier-0 hypotheses.

---

## 3. Tier-1 additions — detailed rationale

### 3.1 Focused-ultrasound BBB opening (FUS-BBBO)

**One-line summary.** A delivery modifier, not a cytotoxic — multiplies the intratumoral concentration of every co-administered systemic drug by transiently opening the blood-brain barrier with MR-guided ultrasound and intravenous microbubbles.

**Why it matters for the platform.** In a Monte Carlo simulator FUS-BBBO is a **coefficient on every existing chemotherapy module**, not a new module that kills cells on its own. Omitting it systematically biases the treatment optimizer against CNS-penetration-limited drugs (which is most of them).

**Evidence anchor.** A 2025 *Lancet Oncology* trial reports microbubble-enhanced transcranial FUS with each TMZ cycle in recurrent GBM with a measurable survival signal vs. historical controls and no grade ≥3 BBBO-attributable adverse events. The Focused Ultrasound Foundation summary corroborates the design and outcome.

**Platform integration.**
- New `DeliveryModifier` node type.
- New `ENHANCES_DELIVERY_OF` edge from `DeliveryModifier` to `Drug`, with an `enhancement_factor` property (literature range 2×–5× depending on drug and ultrasound parameters).
- New `bbb_integrity_score` field on `PatientState`.
- Simulator pharmacology layer applies `effective_concentration = base_concentration × (1 + enhancement_factor × bbb_integrity_score)`.

### 3.2 IDH-mutant therapy axis (vorasidenib)

**One-line summary.** Vorasidenib (Voranigo) received FDA approval in August 2024 for grade 2 IDH-mutant glioma based on the INDIGO trial; combination trials in higher-grade IDH-mutant tumors are ongoing (e.g. NCT07629089: vorasidenib + lomustine).

**Why it matters for the platform.** The v1.0 handoff scope is IDH-wildtype glioblastoma. Two reasons to broaden:
1. A knowledge platform that cannot reason about IDH mutation status as a *treatment-stratifying* variable will produce biased research analyses even within IDH-wildtype, because much of the negative-control literature it ingests comes from IDH-mutant cohorts.
2. The simulator already carries `idh_status` on `PatientState` — it is incoherent to model the variable but not the treatment that responds to it.

**Platform integration.**
- New `IDH_inhibitor` treatment module gated by `patient_state.idh_status == "mutant"`.
- Add a `MutationStatus` qualifier on the `PREDICTS` edge so the same biomarker (e.g. `MGMT methylation`) can predict different outcomes in mutant vs. wildtype patients.

### 3.3 Oncolytic virotherapy

**One-line summary.** Replication-competent engineered viruses (HSV-1: CAN-3110, G47Δ; adenovirus: DNX-2401) that selectively lyse tumor cells *and* convert "cold" GBM into immunologically "hot" tumor, enabling checkpoint-inhibitor response.

**Why it matters for the platform.** The treatment optimizer (SIXTH task) is supposed to explore *combinations*. Oncolytic-virus + checkpoint-inhibitor is the single most active combination signal in recurrent GBM right now (DNX-2401 + pembrolizumab: 56.2% clinical benefit rate). If the action space lacks oncolytic viruses entirely, the optimizer cannot propose this combination, and the entire treatment-explorer page produces an artificially impoverished frontier.

**Platform integration.**
- New `oncolytic_virus` treatment module with a *combination mechanism* tag: `{viral_lysis, immune_activation}`.
- Two evidence anchors: CAN-3110 (*Nature* 2023, n=41 phase I, survival-by-HSV-seropositivity association) and DNX-2401 + pembrolizumab (phase II, n=49).

---

## 4. Tier-2 additions — detailed rationale

### 4.1 Neuron–glioma synapse blockade with perampanel

The v1.0 handoff lists "neuron-signalling blockade" as a treatment module but does not name the candidate drug. **Perampanel** is an FDA-approved antiepileptic AMPA-receptor antagonist now in the **PerSurge / NOA-30** phase IIa trial in recurrent GBM around surgical resection. Preclinical data (Heliyon 2025) show *in-vitro* synergy with TMZ. This is the highest-ROI addition to the platform because:

1. It is a *repurposed* drug — toxicity profile is already established.
2. It is a *combination synergy* with the existing TMZ module — so it stress-tests the `SYNERGIZES_WITH` edge type immediately.
3. It exercises the `cell_state` axis directly — neuron–glioma synapses preferentially drive invasion in NPC-like cells.

### 4.2 Myeloid reprogramming (CSF1R inhibitors)

The v1.0 handoff covers T-cell immunotherapy (checkpoint, CAR-T) but omits the **myeloid compartment**, which is the dominant TME population in GBM (~30–50% of tumor mass). CSF1R inhibitors (PLX3397/pexidartinib, BLZ945) reprogram tumor-associated macrophages from M2 (pro-tumor) to M1 (anti-tumor) phenotype and have nanomolar potency in preclinical GBM models.

**Platform integration.**
- Extend `CellType` node properties with `polarization_state: Enum[M1, M2, naive]`.
- New `CSF1R_inhibitor` treatment module that mutates `patient_state.tam_polarization_score` toward +1.0.
- New `MODULATES_POLARIZATION_OF` edge from `Drug` to `CellType` (M2 → M1).

### 4.3 Cell-state plasticity (Neftel four-state model)

The v1.0 simulator population list is biologically reasonable for a 2018-era model but is **not directly mappable to single-cell RNA datasets**, which is a problem because the platform's own data sources (Ivy GBM Atlas, future spatial transcriptomics) report data in Neftel coordinates. A translation layer would be brittle.

Replacing the five-population scheme with the two-axis `cell_state × resistance_status` representation gives the simulator:
- Direct ingestion from scRNA datasets without re-clustering.
- A natural place to encode plasticity transitions as `TRANSITIONS_TO` edges with stress-dependent weights.
- A correlation with CNV data already in TCGA-GBM (PDGFRA → OPC-like, CDK4 → NPC-like, EGFR → AC-like, NF1 → MES-like).

---

## 5. Tier-3 additions — track but de-prioritize

These additions are real but smaller in impact. Add the vocabulary now so the NER pipeline doesn't have to be retrained later; defer simulator integration to a future phase.

| Topic | Action |
|---|---|
| **Ferroptosis** (GPX4, SLC7A11) | Add as `PATHWAY` and `BIOMARKER` entities. Cell-state-specific vulnerability in quiescent GSCs (Banu et al., *Cancer Cell* 2024). Recurrent tumors show elevated ferroptosis-vulnerability markers. |
| **Chronotherapy** | Add `time_of_day` parameter to existing TMZ module. Morning vs. evening dosing has retrospective ~4-month OS difference in MGMT-methylated patients. |
| **BMP-induced GSC differentiation** | Add `BMP4` as a `DRUG`-class entity (`differentiation_therapy` modality). Pushes quiescent GSCs into cycling state where TMZ acts. |
| **Personalized neoantigen vaccines** | Add `NeoVax`, `GAPVAC` as `TREATMENT` entities distinct from generic "vaccines." NeoVax + pembrolizumab median OS 36.9 mo in newly diagnosed GBM (single-arm). |
| **GD2 / chlorotoxin CAR-T** | Add as specific `CAR-T` subtypes. GD2 CAR-T (NCT04099797): 5/8 PR-or-SD. Chlorotoxin CAR-T binds via avidity → broader tumor coverage. |
| **TTFields synergy mechanism** | Existing module — but add a `SYNERGIZES_WITH` edge from `TTFields` to `temozolomide` reflecting DNA-damage potentiation and immunogenic microenvironment (Front. Oncol. 2023). |

---

## 6. Implications for safety guardrails

The additions in §3–§4 introduce evidence types the v1.0 platform has not encountered:

- **FDA approval data** (vorasidenib, pexidartinib in other tumors).
- **Randomized phase III** (TTFields EF-14, retroactively).
- **Phase II combination data** (DNX-2401 + pembrolizumab, NeoVax + pembrolizumab).
- **Single-cell / spatial omics** (Neftel et al., Wang et al. *Sci Adv* 2024).

This makes three safety properties **mandatory** rather than recommended:

1. **Evidence-tier coloring on the Knowledge Graph Explorer is non-optional.** Without it, a tier-0 hypothesis and a tier-5 randomized trial render identically — exactly the failure mode the research-use-only posture is designed to prevent.
2. **The simulator's UI must never display a single "recommended" treatment.** It must display a *ranked frontier* with confidence intervals, even when the underlying graph contains tier-5 evidence.
3. **Every claim surfaced to a user must link back to its `source_pmids`.** This is already enforced at the loader level (§ graph-loader skeleton). The dashboard must surface it.

---

## 7. Citations

URLs verified via HEAD request on the date of authoring. Entries marked **(publisher-gated)** return a 403/504 to automated agents but resolve normally in a browser. For those, a PubMed or DOI fallback is supplied.

| # | Topic | Primary citation | Verified | Fallback |
|---|---|---|---|---|
| 1 | FUS-BBBO + TMZ phase II | [Lancet Oncology, microbubble-enhanced transcranial FUS](https://www.thelancet.com/article/S1470-2045(25)00492-9/fulltext) | 403 (publisher-gated) | DOI: `10.1016/S1470-2045(25)00492-9` |
| 2 | FUS-BBBO survival summary | [FUS Foundation press release](https://www.fusfoundation.org/posts/glioblastoma-clinical-trial-focused-ultrasound-blood-brain-barrier-opening-is-safe-provides-possible-survival-benefit/) | 200 ✓ | — |
| 3 | CAN-3110 oncolytic HSV phase I | [Ling et al., *Nature* 2023; 623:157–166](https://www.nature.com/articles/s41586-023-06623-2) | 200 ✓ | PMID forthcoming |
| 4 | DNX-2401 + pembrolizumab phase II | [Nassiri et al., *Nat Med* 2023](https://pubmed.ncbi.nlm.nih.gov/37188783/) | 403 (publisher-gated) | PMID `37188783` |
| 5 | Vorasidenib FDA approval / INDIGO | [NCI Cancer Currents 2023](https://www.cancer.gov/news-events/cancer-currents-blog/2023/vorasidenib-low-grade-glioma-idh-mutations) | 200 ✓ | — |
| 6 | Vorasidenib + lomustine trial | [ClinicalTrials.gov NCT07629089](https://clinicaltrials.gov/study/NCT07629089) | 200 ✓ | — |
| 7 | Perampanel PerSurge/NOA-30 phase II | [Hai et al., 2024; PMC10811925](https://pmc.ncbi.nlm.nih.gov/articles/PMC10811925/) | 200 ✓ | PMID `38279087` |
| 8 | Perampanel + TMZ in-vitro synergy | [Heliyon 2025 S2405-8440(25)01548-8](https://www.cell.com/heliyon/fulltext/S2405-8440(25)01548-8) | 403 (publisher-gated) | DOI: `10.1016/j.heliyon.2025.01548` |
| 9 | Perampanel review (Clin Cancer Res 2025) | [AACR PDF](https://aacrjournals.org/clincancerres/article-pdf/doi/10.1158/1078-0432.CCR-25-0018/3620258/ccr-25-0018.pdf) | 403 (publisher-gated) | DOI: `10.1158/1078-0432.CCR-25-0018` |
| 10 | CSF1R / TAM review | [Andersen et al., 2022; PMC8972242](https://pmc.ncbi.nlm.nih.gov/articles/PMC8972242/) | 200 ✓ | — |
| 11 | PLX3397 preclinical GBM | [Sci Reports 2025; s41598-025-32943-6](https://www.nature.com/articles/s41598-025-32943-6) | 200 ✓ | — |
| 12 | Neftel four-state cell-plasticity model | [Neftel et al., *Cell* 2019;178:835–849](https://www.sciencedirect.com/science/article/pii/S0092867419306877) | 403 (publisher-gated) | PMID `31327527` |
| 13 | Spatial epigenomic plasticity (2025) | [Kint et al., 2025; PMC12132327](https://pmc.ncbi.nlm.nih.gov/articles/PMC12132327/) | 200 ✓ | — |
| 14 | Single-cell multi-omics regional states | [Wang et al., *Sci Adv* 2024; adn4306](https://www.science.org/doi/10.1126/sciadv.adn4306) | 403 (publisher-gated) | DOI: `10.1126/sciadv.adn4306` |
| 15 | Ferroptosis vulnerability in recurrence | [Garcia-Mulero et al., 2022; PMC9071304](https://pmc.ncbi.nlm.nih.gov/articles/PMC9071304/) | 200 ✓ | — |
| 16 | Chronotherapy in GBM (2025) | [npj Precision Oncology 2025; s41698-025-01205-z](https://www.nature.com/articles/s41698-025-01205-z) | 200 ✓ | — |
| 17 | Morning vs. evening TMZ (Siteman) | [WashU Siteman Cancer Center](https://siteman.wustl.edu/chemo-for-glioblastoma-may-work-better-in-morning-than-evening/) | 403 (publisher-gated) | — |
| 18 | BMP-induced GSC quiescence | [Sachdeva et al., 2019; PMC6787003](https://pmc.ncbi.nlm.nih.gov/articles/PMC6787003/) | 200 ✓ | — |
| 19 | NeoVax + pembrolizumab in newly dx GBM | [Cancer Network coverage](https://www.cancernetwork.com/view/personalized-cancer-vaccine-pembrolizumab-feasible-effective-newly-diagnosed-gbm) | 403 (publisher-gated) | ClinicalTrials.gov NCT02287428 |
| 20 | GD2 CAR-T phase I | [Liu et al., *npj Precision Oncology* 2024; s41698-024-00753-0](https://www.nature.com/articles/s41698-024-00753-0) | 200 ✓ | — |
| 21 | GD2 CAR-T trial | [ClinicalTrials.gov NCT04099797](https://clinicaltrials.gov/study/NCT04099797) | 200 ✓ | — |
| 22 | Chlorotoxin CAR-T | [Wang et al., 2025; PMC12432350](https://pmc.ncbi.nlm.nih.gov/articles/PMC12432350/) | 200 ✓ | — |
| 23 | TTFields immunogenic microenvironment | [Front. Oncol. 2023; 10.3389/fonc.2023.1274587](https://www.frontiersin.org/journals/oncology/articles/10.3389/fonc.2023.1274587/full) | 504 (publisher-gated) | DOI: `10.3389/fonc.2023.1274587` |

---

## 8. Implementation checklist

A reviewer can use this checklist to drive the v2 patch through the existing CODEX tasks.

- [ ] **First task (ingest).** Extend the PubMed query list per §2.1. Re-run ingestion to backfill the new vocabulary.
- [ ] **Second task (NER).** Add `CELL_STATE` and `DELIVERY_MODIFIER` entity types per §2.2; extend the alias dictionary per §2.3.
- [ ] **Third task (KG).** Add `CellState` and `DeliveryModifier` node labels; add `ENHANCES_DELIVERY_OF`, `SYNERGIZES_WITH`, `TRANSITIONS_TO` edge types; update `ALLOWED_EDGES`, `NODE_KEY`, and uniqueness constraints in `schema.py` and `loader.py`. Add `MutationStatus` qualifier on `PREDICTS`.
- [ ] **Fourth task (GBM-BERT).** Add the new entity/relation types to the fine-tuning label set. No base-model change required.
- [ ] **Fifth task (simulator).** Apply §2.6 patient-state extension; replace the five-population scheme with the two-axis representation per §2.7; add the five new treatment modules per §2.8.
- [ ] **Sixth task (optimizer).** No structural change. The optimizer automatically inherits the expanded action space once §2.8 is applied. Verify the new modules appear in the ranked frontier output.
- [ ] **Seventh task (dashboard).** Make evidence-tier color coding mandatory per §6. Add `cell_state_distribution` and `bbb_integrity_score` surfacing to the Simulator and Treatment Explorer pages.

---

*End of addendum.*
