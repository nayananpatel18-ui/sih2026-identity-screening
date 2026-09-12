"""M15 advisory AI-risk reasoning over an explicitly sanitized evidence payload.

The default adapter is deterministic and makes no network calls.  A future
provider must implement ``AIRiskReasoningAdapter`` and consume only
``SanitizedReasoningPayload``; it must never receive a canonical sample.
"""

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from pydantic import BaseModel, Field

from app.data.models import (
    AIRiskReasoningResult, ConflictItem, ConflictType,
    EvidenceSignal, EvidenceState, RiskLevel,
)
class SanitizedEvidenceSummary(BaseModel):
    """Explicitly allow-listed evidence properties suitable for advisory use."""
    source: str
    category: str
    evidence_state: str
    severity: str
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    limitation: Optional[str] = None


class SanitizedConflictSummary(BaseModel):
    """Conflict metadata without source values or other document content."""
    source_a: str
    source_b: str
    field_name: str
    conflict_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    resolution_status: str
    explanation: str


class SanitizedReasoningPayload(BaseModel):
    """The complete, allow-listed input contract for M15 providers."""
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    evidence_signals: List[SanitizedEvidenceSummary] = Field(default_factory=list)
    conflicts: List[SanitizedConflictSummary] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    recommendation_context: str = ""


def build_sanitized_reasoning_payload(
    *, risk_level: RiskLevel, risk_score: float, uncertainty_score: float,
    signals: Iterable[EvidenceSignal], conflicts: Iterable[ConflictItem],
    recommendation: str,
) -> SanitizedReasoningPayload:
    """Build an allow-listed payload; raw details and evaluation metadata never cross M15."""
    safe_signals = [SanitizedEvidenceSummary(
        source=signal.source, category=signal.category.value,
        evidence_state=signal.evidence_state.value, severity=signal.severity.value,
        title=signal.title, description=signal.description, confidence=signal.confidence,
        limitation=signal.limitation,
    )
    for signal in signals if signal.source != "EVIDENCE_FUSION"]
    safe_conflicts = [SanitizedConflictSummary(
        source_a=conflict.source_a, source_b=conflict.source_b,
        field_name=conflict.field_name, conflict_type=conflict.conflict_type.value,
        severity=conflict.severity.value, confidence=conflict.confidence, impact=conflict.impact,
        resolution_status=conflict.resolution_status, explanation=conflict.explanation,
    ) for conflict in conflicts]
    # No extracted document fields are needed for the local advisory. This excludes
    # raw OCR, MRZ strings, names, document numbers, dates, and conflict values.
    limitations = list(dict.fromkeys(
        signal.limitation for signal in safe_signals if signal.limitation
    ))
    return SanitizedReasoningPayload(
        risk_level=risk_level, risk_score=risk_score, uncertainty_score=uncertainty_score,
        evidence_signals=safe_signals, conflicts=safe_conflicts,
        limitations=limitations, recommendation_context=recommendation,
    )


class AIRiskReasoningAdapter(ABC):
    """Provider boundary. Implementations receive no internal sample or credentials."""

    @abstractmethod
    def assess(self, payload: SanitizedReasoningPayload) -> AIRiskReasoningResult:
        raise NotImplementedError


class DeterministicAIRiskReasoningAdapter(AIRiskReasoningAdapter):
    """Local repeatable evidence summary; never calls a network or an LLM."""

    def assess(self, payload: SanitizedReasoningPayload) -> AIRiskReasoningResult:
        negative = [s for s in payload.evidence_signals if s.evidence_state == EvidenceState.NEGATIVE.value]
        positive = [s for s in payload.evidence_signals if s.evidence_state == EvidenceState.POSITIVE.value]
        uncertain = [s for s in payload.evidence_signals if s.evidence_state in {
            EvidenceState.MISSING.value, EvidenceState.UNAVAILABLE.value, EvidenceState.UNRELIABLE.value
        }]
        contradictions = [c for c in payload.conflicts if c.conflict_type == ConflictType.ACTUAL_CONTRADICTION.value]
        risk_factors = self._unique([self._signal_text(s) for s in negative])
        supporting = self._unique([self._signal_text(s) for s in positive])
        uncertainty = self._unique([self._uncertainty_text(s) for s in uncertain])
        conflict_text = self._unique([self._conflict_text(c) for c in contradictions])
        recommendations = self._recommendations(contradictions, uncertain, negative, payload.uncertainty_score)
        limitations = self._unique(payload.limitations + [s.limitation for s in uncertain if s.limitation])
        summary = self._summary(payload, risk_factors, supporting, uncertainty, conflict_text)
        confidence = self._confidence(payload, uncertainty)
        return AIRiskReasoningResult(
            reasoning_summary=summary, key_risk_factors=risk_factors,
            supporting_evidence=supporting, uncertainty_factors=uncertainty,
            conflicting_evidence=conflict_text, recommended_verifications=recommendations,
            confidence=confidence, limitations=limitations, human_decision_required=True,
        )

    @staticmethod
    def _signal_text(signal: SanitizedEvidenceSummary) -> str:
        return f"{signal.source}: {signal.title} ({signal.description})"

    @staticmethod
    def _uncertainty_text(signal: SanitizedEvidenceSummary) -> str:
        detail = signal.limitation or signal.title
        return f"{signal.source}: evidence is {signal.evidence_state.lower()}; {detail}."

    @staticmethod
    def _conflict_text(conflict: SanitizedConflictSummary) -> str:
        return (f"Detected inconsistency for {conflict.field_name} between "
                f"{conflict.source_a} and {conflict.source_b}: {conflict.explanation}")

    def _summary(self, payload, risks, support, uncertainty, conflicts) -> str:
        if conflicts:
            return "Advisory assessment: supplied evidence contains detected inconsistencies requiring manual verification."
        if uncertainty or payload.risk_level == RiskLevel.GREY:
            return "Advisory assessment: evidence is insufficient or reliability is limited; manual verification is recommended."
        if risks:
            return "Advisory assessment: supplied evidence contains suspicious signals; secondary verification is recommended."
        if support:
            return "Advisory assessment: supplied evidence is consistent and supports the deterministic low-risk result; an officer must still decide."
        return "Advisory assessment: no usable evidence was supplied for additional reasoning; manual verification is recommended."

    def _recommendations(self, conflicts, uncertain, negative, uncertainty_score) -> List[str]:
        recommendations = []
        for conflict in conflicts:
            recommendations.append(f"Manually resolve the {conflict.field_name} inconsistency using authorized sources.")
        if uncertain or uncertainty_score >= 0.65:
            recommendations.append("Obtain clearer or additional verification evidence where available.")
        if negative:
            recommendations.append("Perform secondary inspection of the cited suspicious signals.")
        return self._unique(recommendations)

    @staticmethod
    def _confidence(payload, uncertainty) -> float:
        if not payload.evidence_signals:
            return 0.0
        signal_confidence = sum(s.confidence for s in payload.evidence_signals) / len(payload.evidence_signals)
        return round(max(0.0, min(1.0, signal_confidence * (1.0 - payload.uncertainty_score * 0.5) - len(uncertainty) * 0.03)), 2)

    @staticmethod
    def _unique(values: Iterable[Optional[str]]) -> List[str]:
        return list(dict.fromkeys(value for value in values if value))[:5]


def get_ai_risk_reasoning_adapter(provider: str = "deterministic-local") -> AIRiskReasoningAdapter:
    """Configuration point for a future explicitly enabled provider; no implicit network fallback."""
    if provider != "deterministic-local":
        raise ValueError(f"Unsupported M15 reasoning provider: {provider}")
    return DeterministicAIRiskReasoningAdapter()


def unavailable_ai_risk_reasoning() -> AIRiskReasoningResult:
    """Safe response for an enabled advisory provider that cannot run."""
    return AIRiskReasoningResult(
        provider="unavailable",
        reasoning_summary="Advisory AI reasoning was unavailable. Deterministic screening remains authoritative.",
        uncertainty_factors=["AI advisory reasoning was unavailable; rely on deterministic evidence and manual review."],
        recommended_verifications=["Continue with the deterministic recommendation and officer review."],
        confidence=0.0,
        limitations=["No advisory reasoning was available for this screening."],
        human_decision_required=True,
    )
