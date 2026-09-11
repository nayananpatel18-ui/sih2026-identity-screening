"""
Explanation Engine.

Generates human-readable, evidence-supported explanations for screening results.
Every explanation statement is grounded in specific evidence signals and conflicts.
No unsupported speculation is produced.
"""

from typing import List
from app.data.models import (
    EvidenceSignal,
    ConflictItem,
    RiskLevel,
    EvidenceState,
    ConflictType,
    SignalSeverity,
    BiometricMatchResult,
)


def generate_explanation(
    risk_level: RiskLevel,
    risk_score: float,
    uncertainty_score: float,
    signals: List[EvidenceSignal],
    conflicts: List[ConflictItem],
    biometric_result: BiometricMatchResult,
) -> str:
    """
    Builds a structured natural-language explanation citing evidence signals.
    All claims are bounded by the available evidence.
    """
    parts = []

    # Opening: overall outcome context
    outcome_preamble = {
        RiskLevel.GREEN: "Evidence review is consistent across available document sources.",
        RiskLevel.AMBER: "Screening identified suspicious signals that warrant further officer attention.",
        RiskLevel.RED: "Screening identified multiple strong suspicious signals and unresolved conflicts. Secondary officer inspection is recommended.",
        RiskLevel.GREY: "Insufficient or unreliable evidence. Automated assessment cannot be relied upon.",
    }
    parts.append(outcome_preamble[risk_level])

    # Quality / uncertainty context
    if risk_level == RiskLevel.GREY:
        unreliable = [s for s in signals if s.evidence_state in (EvidenceState.UNRELIABLE, EvidenceState.UNAVAILABLE)]
        if unreliable:
            titles = "; ".join(s.title for s in unreliable[:3])
            parts.append(f"The following signals could not be reliably assessed: {titles}.")
        parts.append("Manual document re-capture and officer examination is required before any determination can be made.")
        return " ".join(parts)

    # Positive signals summary
    positive = [s for s in signals if s.evidence_state == EvidenceState.POSITIVE]
    if positive:
        pos_titles = "; ".join(s.title for s in positive[:4])
        parts.append(f"Consistent signals: {pos_titles}.")

    # Negative signals
    negative = [s for s in signals if s.evidence_state == EvidenceState.NEGATIVE]
    for sig in negative:
        parts.append(f"Suspicious signal — {sig.title}: {sig.description}")
        if sig.limitation:
            parts.append(f"[Limitation: {sig.limitation}]")

    # Explicit conflicts
    contradictions = [c for c in conflicts if c.conflict_type == ConflictType.ACTUAL_CONTRADICTION]
    for conflict in contradictions:
        parts.append(
            f"Conflict detected in '{conflict.field_name}': "
            f"Source A ({conflict.source_a}) reports '{conflict.value_a}' — "
            f"Source B ({conflict.source_b}) reports '{conflict.value_b}'. "
            f"Resolution status: {conflict.resolution_status}."
        )

    # Biometric context
    if biometric_result == BiometricMatchResult.MISMATCH:
        parts.append("Biometric similarity between document portrait and live photo indicates a possible mismatch. This is a supporting signal only and does not constitute proof of identity fraud.")
    elif biometric_result == BiometricMatchResult.INCONCLUSIVE:
        parts.append("Biometric comparison was inconclusive due to image quality limitations.")
    elif biometric_result == BiometricMatchResult.UNAVAILABLE:
        parts.append("No live person photo was provided. Biometric verification was not performed.")

    # Closing
    parts.append(
        "Risk and uncertainty scores are decision-support metrics for officer use. "
        "Final identity determination remains solely with the border security officer."
    )

    return " ".join(parts)
