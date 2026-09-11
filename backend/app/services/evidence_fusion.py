"""M10 deterministic, explainable fusion of existing evidence and conflicts.

The service does not replace individual adapters or the risk engine.  It
classifies the evidence already supplied, then reuses the existing risk and
uncertainty calculations with a small coverage-based uncertainty adjustment.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from app.data.models import (
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    QualityMetadata,
    RiskLevel,
    SignalCategory,
    SignalSeverity,
)
from app.services.risk_engine import (
    compute_risk_score,
    compute_uncertainty_score,
    determine_risk_level,
    get_recommendation,
)


@dataclass
class EvidenceFusionResult:
    risk_score: float
    uncertainty_score: float
    risk_level: RiskLevel
    coverage: Dict[str, Any]
    strongest_positive: List[Dict[str, Any]]
    strongest_negative: List[Dict[str, Any]]
    important_conflicts: List[Dict[str, Any]]
    uncertainty_reasons: List[str]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "uncertainty_score": self.uncertainty_score,
            "risk_level": self.risk_level.value,
            "coverage": self.coverage,
            "strongest_positive": self.strongest_positive,
            "strongest_negative": self.strongest_negative,
            "important_conflicts": self.important_conflicts,
            "uncertainty_reasons": self.uncertainty_reasons,
            "recommendation": self.recommendation,
        }


class MultimodalEvidenceFusionEngine:
    """Fuses heterogeneous evidence without changing the decision thresholds."""

    def fuse(
        self,
        signals: List[EvidenceSignal],
        conflicts: List[ConflictItem],
        quality: QualityMetadata,
    ) -> EvidenceFusionResult:
        coverage = self._coverage(signals, conflicts)
        risk_score = compute_risk_score(signals, conflicts)
        uncertainty_score = compute_uncertainty_score(quality, signals, conflicts)
        uncertainty_reasons = self._uncertainty_reasons(signals, conflicts)

        if not signals:
            uncertainty_score = max(uncertainty_score, 0.70)
            uncertainty_reasons.append("No evidence signals were available for assessment.")
        elif coverage["missing_count"]:
            # Missing evidence is never risk-bearing; it is only a bounded
            # coverage limitation when some evidence is absent.
            missing_adjustment = min(coverage["missing_count"] / coverage["signal_count"] * 0.15, 0.15)
            uncertainty_score = min(1.0, round(uncertainty_score + missing_adjustment, 4))
            uncertainty_reasons.append("Some evidence inputs were missing, limiting coverage without indicating fraud.")

        uncertain_conflicts = [
            conflict for conflict in conflicts
            if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION and conflict.confidence < 0.70
        ]
        if uncertain_conflicts:
            uncertainty_score = min(1.0, round(uncertainty_score + min(0.10, 0.05 * len(uncertain_conflicts)), 4))
            uncertainty_reasons.append("One or more contradictions have limited reliability and remain unresolved.")

        risk_level = determine_risk_level(risk_score, uncertainty_score)
        return EvidenceFusionResult(
            risk_score=risk_score,
            uncertainty_score=uncertainty_score,
            risk_level=risk_level,
            coverage=coverage,
            strongest_positive=self._strongest(signals, EvidenceState.POSITIVE),
            strongest_negative=self._strongest(signals, EvidenceState.NEGATIVE),
            important_conflicts=self._important_conflicts(conflicts),
            uncertainty_reasons=uncertainty_reasons,
            recommendation=get_recommendation(risk_level),
        )

    @staticmethod
    def _coverage(signals: List[EvidenceSignal], conflicts: List[ConflictItem]) -> Dict[str, Any]:
        counts = {state.value.lower(): 0 for state in EvidenceState}
        for signal in signals:
            counts[signal.evidence_state.value.lower()] += 1
        return {
            "signal_count": len(signals),
            "positive_count": counts["positive"],
            "negative_count": counts["negative"],
            "missing_count": counts["missing"],
            "unavailable_count": counts["unavailable"],
            "unreliable_count": counts["unreliable"],
            "not_applicable_count": counts["not_applicable"],
            "conflict_count": len(conflicts),
            "sources": sorted({signal.source for signal in signals}),
        }

    @staticmethod
    def _signal_summary(signal: EvidenceSignal) -> Dict[str, Any]:
        return {
            "source": signal.source,
            "title": signal.title,
            "severity": signal.severity.value,
            "confidence": signal.confidence,
            "contribution": signal.contribution,
        }

    def _strongest(self, signals: List[EvidenceSignal], state: EvidenceState) -> List[Dict[str, Any]]:
        filtered = [signal for signal in signals if signal.evidence_state == state]
        return [self._signal_summary(signal) for signal in sorted(
            filtered,
            key=lambda signal: (signal.contribution * signal.confidence, signal.confidence),
            reverse=True,
        )[:3]]

    @staticmethod
    def _important_conflicts(conflicts: List[ConflictItem]) -> List[Dict[str, Any]]:
        meaningful = [conflict for conflict in conflicts if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION]
        return [{
            "field_name": conflict.field_name,
            "source_a": conflict.source_a,
            "source_b": conflict.source_b,
            "severity": conflict.severity.value,
            "confidence": conflict.confidence,
            "impact": conflict.impact,
            "resolution_status": conflict.resolution_status,
        } for conflict in sorted(meaningful, key=lambda conflict: conflict.impact * conflict.confidence, reverse=True)[:3]]

    @staticmethod
    def _uncertainty_reasons(signals: List[EvidenceSignal], conflicts: List[ConflictItem]) -> List[str]:
        reasons: List[str] = []
        for state, description in (
            (EvidenceState.UNRELIABLE, "Some evidence was unreliable and should be reviewed manually."),
            (EvidenceState.UNAVAILABLE, "Some analysis could not be performed."),
        ):
            if any(signal.evidence_state == state for signal in signals):
                reasons.append(description)
        if any(conflict.conflict_type in (ConflictType.UNREADABLE_EVIDENCE, ConflictType.UNRELIABLE_EVIDENCE) for conflict in conflicts):
            reasons.append("Some comparisons were not reliable enough for a definitive conclusion.")
        return reasons


def fusion_evidence_signal(result: EvidenceFusionResult) -> EvidenceSignal:
    """Expose the fused assessment through the existing officer-facing evidence model."""
    if result.risk_level == RiskLevel.GREY:
        state, title = EvidenceState.UNRELIABLE, "Multimodal Evidence Fusion Inconclusive"
        description = "Available evidence could not support a sufficiently reliable fused assessment. Manual verification is recommended."
    elif result.risk_score > 0:
        state, title = EvidenceState.NEGATIVE, "Multimodal Evidence Fusion Identified Suspicious Signals"
        description = "Fused evidence includes bounded suspicious signals or unresolved contradictions requiring officer review."
    else:
        state, title = EvidenceState.POSITIVE, "Multimodal Evidence Fusion Completed"
        description = "Available evidence was fused into a consistent decision-support assessment."
    return EvidenceSignal(
        signal_id="SIG_EVIDENCE_FUSION_RUNTIME",
        source="EVIDENCE_FUSION",
        category=SignalCategory.DOCUMENT_INTELLIGENCE,
        evidence_state=state,
        severity=SignalSeverity.INFO,
        title=title,
        description=description,
        confidence=1.0,
        contribution=0.0,
        limitation="Fusion summarizes existing evidence and conflicts; it does not independently authenticate a document or make a legal decision.",
        raw_details=result.to_dict(),
    )
