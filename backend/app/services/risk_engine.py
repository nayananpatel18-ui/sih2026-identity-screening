"""
Dual-Axis Risk & Uncertainty Engine.

Evaluates evidence signals and conflicts across two independent dimensions:
  risk_score        (0.0 = lowest suspicion, 1.0 = highest suspicion)
  uncertainty_score (0.0 = confident assessment, 1.0 = unreliable / insufficient evidence)

Decision precedence:
  GREY  takes precedence when uncertainty_score >= 0.65
  RED   when uncertainty_score < 0.65 and risk_score >= 0.70
  AMBER when uncertainty_score < 0.65 and risk_score >= 0.35
  GREEN when uncertainty_score < 0.65 and risk_score < 0.35

Cautious decision semantics:
  GREEN -> Low Risk / Evidence Consistent   -> Routine Clearance Recommended
  AMBER -> Suspicious Signals               -> Further Verification Recommended
  RED   -> Multiple Suspicious Signals /
           Unresolved High-Impact Conflicts  -> Secondary Inspection Recommended
  GREY  -> High Uncertainty / Insufficient
           or Unreliable Evidence            -> Manual Officer Review Required
"""

from typing import List, Tuple
from app.data.models import (
    EvidenceSignal,
    ConflictItem,
    EvidenceState,
    ConflictType,
    RiskLevel,
    QualityMetadata,
    SignalSeverity,
)

# Decision thresholds
UNCERTAINTY_GREY_THRESHOLD = 0.65
RISK_RED_THRESHOLD = 0.70
RISK_AMBER_THRESHOLD = 0.35


def compute_uncertainty_score(
    quality: QualityMetadata,
    signals: List[EvidenceSignal],
    conflicts: List[ConflictItem],
) -> float:
    """
    Computes uncertainty from image quality metrics and signal reliability.
    High uncertainty routes to GREY regardless of risk_score.
    """
    score = 0.0

    # Quality-based penalties
    score += quality.blur_score * 0.40
    if quality.glare_detected:
        score += 0.15
    if quality.is_partial:
        score += 0.20
    if not quality.is_sufficient_quality:
        score += 0.30

    # Signal reliability penalties: count UNRELIABLE and UNAVAILABLE signals
    unreliable_count = sum(
        1 for s in signals
        if s.evidence_state in (EvidenceState.UNRELIABLE, EvidenceState.UNAVAILABLE)
    )
    total_signals = max(len(signals), 1)
    score += (unreliable_count / total_signals) * 0.30

    # Unreadable or unreliable comparisons are a limitation of the evidence,
    # not a contradiction and not a fraud indicator. Missing comparisons do
    # not add a penalty.
    unreliable_conflicts = [
        conflict for conflict in conflicts
        if conflict.conflict_type in (
            ConflictType.UNREADABLE_EVIDENCE,
            ConflictType.UNRELIABLE_EVIDENCE,
        )
    ]
    score += min(
        sum(conflict.impact * conflict.confidence for conflict in unreliable_conflicts),
        0.30,
    )

    return round(min(score, 1.0), 4)


def compute_risk_score(
    signals: List[EvidenceSignal],
    conflicts: List[ConflictItem],
) -> float:
    """
    Computes risk score from NEGATIVE evidence signals and ACTUAL_CONTRADICTION conflicts.
    UNRELIABLE / MISSING signals do NOT raise risk_score — they raise uncertainty_score.
    """
    score = 0.0

    # Contribution-weighted sum from NEGATIVE signals
    for sig in signals:
        if sig.evidence_state == EvidenceState.NEGATIVE:
            score += sig.contribution * sig.confidence

    # Direct impact from ACTUAL_CONTRADICTION conflicts only
    for conflict in conflicts:
        if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION:
            score += conflict.impact * conflict.confidence

    return round(min(score, 1.0), 4)


def determine_risk_level(risk_score: float, uncertainty_score: float) -> RiskLevel:
    """
    Four-state decision matrix with GREY precedence.
    """
    if uncertainty_score >= UNCERTAINTY_GREY_THRESHOLD:
        return RiskLevel.GREY
    if risk_score >= RISK_RED_THRESHOLD:
        return RiskLevel.RED
    if risk_score >= RISK_AMBER_THRESHOLD:
        return RiskLevel.AMBER
    return RiskLevel.GREEN


def get_recommendation(level: RiskLevel) -> str:
    """
    Returns cautious, decision-support wording. Never claims autonomous legal authority.
    """
    return {
        RiskLevel.GREEN: "ROUTINE CLEARANCE RECOMMENDED — Evidence is consistent. Officer may proceed with standard procedures. Final decision remains with the officer.",
        RiskLevel.AMBER: "FURTHER VERIFICATION RECOMMENDED — Suspicious signals detected. Officer attention recommended before proceeding.",
        RiskLevel.RED: "SECONDARY INSPECTION RECOMMENDED — Multiple strong suspicious signals or unresolved high-impact conflicts detected. AI assessment indicates high suspicion. Final determination requires officer review.",
        RiskLevel.GREY: "MANUAL OFFICER REVIEW REQUIRED — Evidence is insufficient, unreliable, or of poor quality. Automated assessment cannot be relied upon. Human evaluation and re-capture recommended.",
    }[level]
