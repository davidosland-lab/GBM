"""Rule definitions for baseline biomedical relation extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern

from gbmbert.knowledge_graph.schema import NodeLabel, RelationType


@dataclass(frozen=True)
class RelationRule:
    """A trigger-pattern rule for a schema-valid relation type."""

    relation: RelationType
    triggers: tuple[Pattern[str], ...]
    label_pairs: tuple[tuple[NodeLabel, NodeLabel], ...]
    confidence: float = 0.55

    def match(self, text: str) -> str | None:
        for trigger in self.triggers:
            match = trigger.search(text)
            if match:
                return match.group(0)
        return None


def _patterns(*phrases: str) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(phrase, flags=re.IGNORECASE) for phrase in phrases)


RELATION_RULES: tuple[RelationRule, ...] = (
    RelationRule(
        relation=RelationType.PREDICTS,
        triggers=_patterns(
            r"\bpredicts?\b",
            r"\bpredicted\b",
            r"\bpredictive of\b",
            r"\bbiomarker[s]? of response\b",
        ),
        label_pairs=(
            (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
            (NodeLabel.GENE, NodeLabel.OUTCOME),
            (NodeLabel.DISEASE, NodeLabel.OUTCOME),
        ),
        confidence=0.62,
    ),
    RelationRule(
        relation=RelationType.ASSOCIATED_WITH,
        triggers=_patterns(
            r"\bassociated with\b",
            r"\bassociation with\b",
            r"\bcorrelates? with\b",
            r"\bcorrelated with\b",
            r"\blinked to\b",
        ),
        label_pairs=(
            (NodeLabel.GENE, NodeLabel.DISEASE),
            (NodeLabel.GENE, NodeLabel.OUTCOME),
            (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
            (NodeLabel.BIOMARKER, NodeLabel.DISEASE),
            (NodeLabel.CELL_TYPE, NodeLabel.OUTCOME),
            (NodeLabel.CELL_STATE, NodeLabel.OUTCOME),
            (NodeLabel.PATHWAY, NodeLabel.DISEASE),
            (NodeLabel.TRIAL, NodeLabel.TREATMENT),
        ),
        confidence=0.58,
    ),
    RelationRule(
        relation=RelationType.TARGETS,
        triggers=_patterns(
            r"\btargets?\b",
            r"\btargeting\b",
            r"\btargeted\b",
        ),
        label_pairs=(
            (NodeLabel.DRUG, NodeLabel.GENE),
            (NodeLabel.TREATMENT, NodeLabel.GENE),
            (NodeLabel.DRUG, NodeLabel.PATHWAY),
            (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
        ),
        confidence=0.6,
    ),
    RelationRule(
        relation=RelationType.INHIBITS,
        triggers=_patterns(
            r"\binhibits?\b",
            r"\binhibited\b",
            r"\binhibition of\b",
            r"\bblocks?\b",
            r"\bblockade of\b",
        ),
        label_pairs=(
            (NodeLabel.GENE, NodeLabel.PATHWAY),
            (NodeLabel.DRUG, NodeLabel.PATHWAY),
            (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
            (NodeLabel.PATHWAY, NodeLabel.PATHWAY),
        ),
        confidence=0.6,
    ),
    RelationRule(
        relation=RelationType.ACTIVATES,
        triggers=_patterns(
            r"\bactivates?\b",
            r"\bactivated\b",
            r"\bactivation of\b",
            r"\bpromotes?\b",
        ),
        label_pairs=(
            (NodeLabel.GENE, NodeLabel.PATHWAY),
            (NodeLabel.DRUG, NodeLabel.PATHWAY),
            (NodeLabel.TREATMENT, NodeLabel.PATHWAY),
            (NodeLabel.PATHWAY, NodeLabel.PATHWAY),
        ),
        confidence=0.6,
    ),
    RelationRule(
        relation=RelationType.IMPROVES,
        triggers=_patterns(
            r"\bimproves?\b",
            r"\bimproved\b",
            r"\bincreases survival\b",
            r"\bprolongs survival\b",
            r"\benhances response\b",
        ),
        label_pairs=(
            (NodeLabel.DRUG, NodeLabel.OUTCOME),
            (NodeLabel.TREATMENT, NodeLabel.OUTCOME),
        ),
        confidence=0.57,
    ),
    RelationRule(
        relation=RelationType.WORSENS,
        triggers=_patterns(
            r"\bworsens?\b",
            r"\bworsened\b",
            r"\bresistance\b",
            r"\btoxicity\b",
        ),
        label_pairs=(
            (NodeLabel.DRUG, NodeLabel.OUTCOME),
            (NodeLabel.TREATMENT, NodeLabel.OUTCOME),
            (NodeLabel.GENE, NodeLabel.OUTCOME),
            (NodeLabel.BIOMARKER, NodeLabel.OUTCOME),
        ),
        confidence=0.54,
    ),
    RelationRule(
        relation=RelationType.ENHANCES_DELIVERY_OF,
        triggers=_patterns(
            r"\benhances? delivery of\b",
            r"\bincreases? delivery of\b",
            r"\bimproves? delivery of\b",
            r"\bblood-brain barrier opening\b",
        ),
        label_pairs=(
            (NodeLabel.DELIVERY_MODIFIER, NodeLabel.DRUG),
            (NodeLabel.DELIVERY_MODIFIER, NodeLabel.TREATMENT),
        ),
        confidence=0.64,
    ),
    RelationRule(
        relation=RelationType.SYNERGIZES_WITH,
        triggers=_patterns(
            r"\bsynergizes? with\b",
            r"\bsynergy with\b",
            r"\bsynergistic with\b",
            r"\bcombined with\b",
            r"\bcombination with\b",
        ),
        label_pairs=(
            (NodeLabel.TREATMENT, NodeLabel.TREATMENT),
            (NodeLabel.DRUG, NodeLabel.DRUG),
            (NodeLabel.DRUG, NodeLabel.TREATMENT),
            (NodeLabel.TREATMENT, NodeLabel.DRUG),
        ),
        confidence=0.56,
    ),
    RelationRule(
        relation=RelationType.TRANSITIONS_TO,
        triggers=_patterns(
            r"\btransitions? to\b",
            r"\bplasticity toward\b",
            r"\bshift[s]? toward\b",
        ),
        label_pairs=((NodeLabel.CELL_STATE, NodeLabel.CELL_STATE),),
        confidence=0.53,
    ),
    RelationRule(
        relation=RelationType.MODULATES_POLARIZATION_OF,
        triggers=_patterns(
            r"\breprograms?\b",
            r"\bpolarization\b",
            r"\bpolarizes?\b",
            r"\bmodulates? polarization\b",
        ),
        label_pairs=(
            (NodeLabel.DRUG, NodeLabel.CELL_TYPE),
            (NodeLabel.TREATMENT, NodeLabel.CELL_TYPE),
        ),
        confidence=0.55,
    ),
)
