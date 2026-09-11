"""Focused M15 tests for deterministic advisory reasoning and its privacy boundary."""

import app.data.synthetic_adapter

from app.data.base import DatasetRegistry
from app.data.models import (
    CanonicalExtractedFields, ConflictItem, ConflictType, EvidenceSignal,
    EvidenceState, RiskLevel, SignalCategory, SignalSeverity,
)
from app.services.ai_risk_reasoning import (
    DeterministicAIRiskReasoningAdapter, build_sanitized_reasoning_payload,
)
from app.services.pipeline import run_screening_pipeline


def _signal(state, title="Check", *, limitation=None, confidence=0.9):
    return EvidenceSignal(
        signal_id=f"SIG-{state.value}", source="TEST", category=SignalCategory.STRUCTURAL_VALIDATION,
        evidence_state=state, severity=SignalSeverity.HIGH if state == EvidenceState.NEGATIVE else SignalSeverity.INFO,
        title=title, description=f"{title} observed", confidence=confidence, contribution=0.5,
        limitation=limitation, raw_details={"ground_truth": "hidden", "tamper_details": "hidden"},
    )


def _assess(level, signals=(), conflicts=(), uncertainty=0.1):
    payload = build_sanitized_reasoning_payload(
        risk_level=level, risk_score=0.8 if level == RiskLevel.RED else 0.1,
        uncertainty_score=uncertainty, signals=signals, conflicts=conflicts,
        extracted_fields=CanonicalExtractedFields(full_name="A Person", document_number="X1"),
        recommendation="Officer review remains required.",
    )
    return payload, DeterministicAIRiskReasoningAdapter().assess(payload)


def test_green_consistent_evidence():
    _, result = _assess(RiskLevel.GREEN, [_signal(EvidenceState.POSITIVE, "MRZ consistent")])
    assert result.supporting_evidence and not result.key_risk_factors
    assert "consistent" in result.reasoning_summary.lower()


def test_amber_suspicious_evidence():
    _, result = _assess(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE, "Visual anomaly")])
    assert result.key_risk_factors and "suspicious" in result.reasoning_summary.lower()


def test_red_strong_conflicting_evidence():
    conflict = ConflictItem(conflict_id="C1", source_a="OCR", source_b="MRZ", field_name="dob",
                            value_a="1990", value_b="1991", conflict_type=ConflictType.ACTUAL_CONTRADICTION,
                            severity=SignalSeverity.CRITICAL, confidence=0.95, impact=0.9,
                            explanation="Values differ.")
    _, result = _assess(RiskLevel.RED, conflicts=[conflict])
    assert result.conflicting_evidence and "inconsisten" in result.reasoning_summary.lower()


def test_grey_insufficient_evidence():
    _, result = _assess(RiskLevel.GREY, uncertainty=0.8)
    assert "insufficient" in result.reasoning_summary.lower()
    assert result.confidence == 0.0


def test_missing_evidence_is_explicitly_uncertain_not_negative():
    _, result = _assess(RiskLevel.GREY, [_signal(EvidenceState.MISSING, "Secondary document")], uncertainty=0.8)
    assert not result.key_risk_factors
    assert "missing" in result.uncertainty_factors[0].lower()


def test_unavailable_evidence_is_explicitly_uncertain_not_negative():
    _, result = _assess(RiskLevel.GREY, [_signal(EvidenceState.UNAVAILABLE, "OCR service", limitation="Service unavailable")], uncertainty=0.8)
    assert not result.key_risk_factors
    assert "unavailable" in result.uncertainty_factors[0].lower()


def test_unreliable_evidence_is_explicitly_uncertain_not_negative():
    _, result = _assess(RiskLevel.GREY, [_signal(EvidenceState.UNRELIABLE, "Portrait", limitation="Image blurred")], uncertainty=0.8)
    assert not result.key_risk_factors
    assert "unreliable" in result.uncertainty_factors[0].lower()


def test_actual_cross_document_contradiction_is_explained():
    conflict = ConflictItem(conflict_id="C2", source_a="Document A", source_b="Document B", field_name="document_number",
                            conflict_type=ConflictType.ACTUAL_CONTRADICTION, severity=SignalSeverity.HIGH,
                            confidence=0.9, impact=0.8, explanation="Numbers do not match.")
    _, result = _assess(RiskLevel.RED, conflicts=[conflict])
    assert "document_number" in result.conflicting_evidence[0]
    assert result.recommended_verifications


def test_deterministic_repeatability():
    signals = [_signal(EvidenceState.NEGATIVE, "Visual anomaly")]
    payload, first = _assess(RiskLevel.AMBER, signals)
    second = DeterministicAIRiskReasoningAdapter().assess(payload)
    assert first.model_dump() == second.model_dump()


def test_ground_truth_privacy_boundary():
    signals = [_signal(EvidenceState.NEGATIVE, "Visual anomaly")]
    payload, result = _assess(RiskLevel.AMBER, signals)
    serialized_input = str(payload.model_dump()).lower()
    serialized_output = str(result.model_dump()).lower()
    for forbidden in ("ground_truth", "expected_risk", "tamper_details", "is_tampered"):
        assert forbidden not in serialized_input
        assert forbidden not in serialized_output


def test_ai_cannot_mutate_deterministic_risk_or_evidence():
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_002_TAMPERED")
    assert sample
    baseline = run_screening_pipeline(sample, enable_cross_document_consistency=True, enable_evidence_fusion=True)
    advised = run_screening_pipeline(sample, enable_cross_document_consistency=True, enable_evidence_fusion=True,
                                     enable_ai_risk_reasoning=True)
    assert baseline.ai_risk_reasoning is None
    assert advised.ai_risk_reasoning is not None
    assert (baseline.risk_level, baseline.risk_score, baseline.uncertainty_score) == (
        advised.risk_level, advised.risk_score, advised.uncertainty_score)
    assert [s.model_dump() for s in baseline.evidence_signals] == [s.model_dump() for s in advised.evidence_signals]
    assert [c.model_dump() for c in baseline.conflicts] == [c.model_dump() for c in advised.conflicts]


def test_existing_pipeline_behavior_is_unchanged_when_m15_is_disabled():
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_001_GENUINE")
    assert sample
    default = run_screening_pipeline(sample, enable_evidence_fusion=True, enable_officer_review=True)
    explicitly_disabled = run_screening_pipeline(sample, enable_evidence_fusion=True, enable_officer_review=True,
                                                 enable_ai_risk_reasoning=False)
    assert default.ai_risk_reasoning is None and explicitly_disabled.ai_risk_reasoning is None
    assert "ai_risk_reasoning" not in default.model_dump()
    assert (default.risk_level, default.risk_score, default.uncertainty_score) == (
        explicitly_disabled.risk_level, explicitly_disabled.risk_score, explicitly_disabled.uncertainty_score)
