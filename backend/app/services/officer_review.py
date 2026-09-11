"""M11 deterministic officer-facing review derived only from screening evidence."""

from typing import Dict, Iterable, List

from app.data.models import (
    ConflictItem,
    ConflictType,
    EvidenceSignal,
    EvidenceState,
    OfficerReviewConflict,
    OfficerReviewFinding,
    OfficerReviewResult,
    RiskLevel,
)


_ASSESSMENTS = {
    RiskLevel.GREEN: "Available evidence is broadly consistent with low observed risk. Routine verification remains an officer decision.",
    RiskLevel.AMBER: "Suspicious signals were identified and secondary verification is recommended before the officer makes a determination.",
    RiskLevel.RED: "Multiple significant suspicious signals or unresolved conflicts were identified; manual or secondary inspection is strongly recommended.",
    RiskLevel.GREY: "Available evidence is insufficient or unreliable for a confident assessment; manual verification is recommended.",
}


class OfficerReviewService:
    """Converts existing evidence and conflicts into concise, traceable review aids."""

    def build(
        self,
        *,
        screening_id: str,
        risk_level: RiskLevel,
        risk_score: float,
        uncertainty_score: float,
        signals: List[EvidenceSignal],
        conflicts: List[ConflictItem],
        recommendation: str,
    ) -> OfficerReviewResult:
        review_signals = [signal for signal in signals if signal.source != "EVIDENCE_FUSION"]
        positive = self._findings(review_signals, EvidenceState.POSITIVE)
        suspicious = self._findings(review_signals, EvidenceState.NEGATIVE)
        review_conflicts = self._conflicts(conflicts)
        uncertainty_reasons = self._uncertainty_reasons(review_signals, conflicts, uncertainty_score)
        return OfficerReviewResult(
            screening_id=screening_id,
            risk_level=risk_level,
            risk_score=risk_score,
            uncertainty_score=uncertainty_score,
            overall_assessment=_ASSESSMENTS[risk_level],
            evidence_summary=self._summary(review_signals, conflicts),
            key_positive_findings=positive,
            key_suspicious_findings=suspicious,
            conflicts=review_conflicts,
            uncertainty_reasons=uncertainty_reasons,
            recommended_verifications=self._recommendations(review_signals, conflicts, uncertainty_reasons),
            limitations=self._limitations(review_signals),
            recommendation=recommendation,
            human_decision_required=True,
        )

    @staticmethod
    def _finding(signal: EvidenceSignal) -> OfficerReviewFinding:
        return OfficerReviewFinding(
            signal_id=signal.signal_id,
            source=signal.source,
            category=signal.category,
            title=signal.title,
            description=signal.description,
            severity=signal.severity,
            confidence=signal.confidence,
            contribution=signal.contribution,
        )

    def _findings(self, signals: Iterable[EvidenceSignal], state: EvidenceState) -> List[OfficerReviewFinding]:
        selected = [signal for signal in signals if signal.evidence_state == state]
        return [self._finding(signal) for signal in sorted(
            selected,
            key=lambda signal: (signal.contribution * signal.confidence, signal.confidence),
            reverse=True,
        )[:3]]

    @staticmethod
    def _conflicts(conflicts: Iterable[ConflictItem]) -> List[OfficerReviewConflict]:
        selected = [conflict for conflict in conflicts if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION]
        return [OfficerReviewConflict(
            conflict_id=conflict.conflict_id,
            field_name=conflict.field_name,
            source_a=conflict.source_a,
            source_b=conflict.source_b,
            value_a=conflict.value_a,
            value_b=conflict.value_b,
            severity=conflict.severity,
            confidence=conflict.confidence,
            impact=conflict.impact,
            resolution_status=conflict.resolution_status,
            explanation="Unresolved conflict detected between supplied evidence sources. " + conflict.explanation,
        ) for conflict in sorted(selected, key=lambda conflict: conflict.impact * conflict.confidence, reverse=True)[:3]]

    @staticmethod
    def _summary(signals: List[EvidenceSignal], conflicts: List[ConflictItem]) -> Dict[str, object]:
        return {
            "signal_count": len(signals),
            "sources": sorted({signal.source for signal in signals}),
            "positive_count": sum(signal.evidence_state == EvidenceState.POSITIVE for signal in signals),
            "negative_count": sum(signal.evidence_state == EvidenceState.NEGATIVE for signal in signals),
            "missing_count": sum(signal.evidence_state == EvidenceState.MISSING for signal in signals),
            "unavailable_count": sum(signal.evidence_state == EvidenceState.UNAVAILABLE for signal in signals),
            "unreliable_count": sum(signal.evidence_state == EvidenceState.UNRELIABLE for signal in signals),
            "conflict_count": len([conflict for conflict in conflicts if conflict.conflict_type == ConflictType.ACTUAL_CONTRADICTION]),
        }

    @staticmethod
    def _uncertainty_reasons(signals: List[EvidenceSignal], conflicts: List[ConflictItem], uncertainty_score: float) -> List[str]:
        reasons: List[str] = []
        for state, prefix in (
            (EvidenceState.MISSING, "Evidence was missing"),
            (EvidenceState.UNAVAILABLE, "Analysis was unavailable"),
            (EvidenceState.UNRELIABLE, "Evidence was unreliable"),
        ):
            for signal in signals:
                if signal.evidence_state == state:
                    detail = signal.limitation or signal.title
                    reasons.append(f"{prefix}: {detail}")
        if any(conflict.conflict_type in (ConflictType.UNREADABLE_EVIDENCE, ConflictType.UNRELIABLE_EVIDENCE) for conflict in conflicts):
            reasons.append("Some evidence comparisons were not reliable enough for a definitive conclusion.")
        if uncertainty_score >= 0.65 and not reasons:
            reasons.append("Available evidence coverage was insufficient for a confident assessment.")
        return OfficerReviewService._unique(reasons, 4)

    @staticmethod
    def _recommendations(signals: List[EvidenceSignal], conflicts: List[ConflictItem], uncertainty_reasons: List[str]) -> List[str]:
        recommendations: List[str] = []
        for conflict in conflicts:
            if conflict.conflict_type != ConflictType.ACTUAL_CONTRADICTION:
                continue
            if conflict.field_name in {"dob", "date_of_birth"}:
                recommendations.append("Verify the date of birth against an authorized source.")
            elif conflict.field_name == "document_number":
                recommendations.append("Verify the document number using authorized procedures.")
            else:
                recommendations.append(f"Manually resolve the {conflict.field_name} discrepancy between supplied evidence sources.")
        for signal in signals:
            if signal.source == "MRZ" and signal.evidence_state in (EvidenceState.NEGATIVE, EvidenceState.UNRELIABLE, EvidenceState.UNAVAILABLE):
                recommendations.append("Manually inspect MRZ characters and document structure.")
            elif signal.source == "BIOMETRIC" and signal.evidence_state in (EvidenceState.UNRELIABLE, EvidenceState.UNAVAILABLE, EvidenceState.MISSING):
                recommendations.append("Perform manual identity verification using authorized procedures.")
            elif signal.source == "VISUAL_FORENSICS" and signal.evidence_state in (EvidenceState.UNRELIABLE, EvidenceState.NEGATIVE):
                recommendations.append("Inspect the document image for quality limitations or visual inconsistencies.")
            elif signal.evidence_state in (EvidenceState.MISSING, EvidenceState.UNAVAILABLE, EvidenceState.UNRELIABLE):
                recommendations.append("Obtain clearer or additional verification evidence where available.")
        if uncertainty_reasons:
            recommendations.append("Document the manual verification outcome before making a final determination.")
        return OfficerReviewService._unique(recommendations, 5)

    @staticmethod
    def _limitations(signals: Iterable[EvidenceSignal]) -> List[str]:
        return OfficerReviewService._unique([signal.limitation for signal in signals if signal.limitation], 5)

    @staticmethod
    def _unique(values: Iterable[str], maximum: int) -> List[str]:
        return list(dict.fromkeys(values))[:maximum]
