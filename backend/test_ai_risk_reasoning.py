"""Focused M15 tests for local, advisory-only risk reasoning."""

import app.data.synthetic_adapter

from app.data.base import DatasetRegistry
from app.data.models import (
    ConflictItem, ConflictType, EvidenceSignal, EvidenceState, RiskLevel,
    SignalCategory, SignalSeverity,
)
from app.services.ai_risk_reasoning import (
    DeterministicAIRiskReasoningAdapter, build_sanitized_reasoning_payload,
    get_ai_risk_reasoning_adapter,
)
from app.services.pipeline import run_screening_pipeline
import app.services.pipeline as pipeline_module


def _signal(state, title="Check", *, limitation=None, confidence=0.9):
    return EvidenceSignal(
        signal_id=f"SIG-{state.value}", source="TEST", category=SignalCategory.STRUCTURAL_VALIDATION,
        evidence_state=state, severity=SignalSeverity.HIGH if state == EvidenceState.NEGATIVE else SignalSeverity.INFO,
        title=title, description=f"{title} observed", confidence=confidence, contribution=0.5,
        limitation=limitation, raw_details={"ground_truth": "hidden", "raw_ocr_text": "secret OCR", "api_key": "secret"},
    )


def _assess(level, signals=(), conflicts=(), uncertainty=0.1):
    payload = build_sanitized_reasoning_payload(
        risk_level=level, risk_score=0.8 if level == RiskLevel.RED else 0.1,
        uncertainty_score=uncertainty, signals=signals, conflicts=conflicts,
        recommendation="Officer review remains required.",
    )
    return payload, DeterministicAIRiskReasoningAdapter().assess(payload)


def test_sanitized_payload_excludes_raw_document_and_evaluation_data():
    conflict = ConflictItem(
        conflict_id="C1", source_a="OCR", source_b="MRZ", field_name="document_number",
        value_a="SECRET-A", value_b="SECRET-B", conflict_type=ConflictType.ACTUAL_CONTRADICTION,
        severity=SignalSeverity.HIGH, confidence=0.9, impact=0.8, explanation="Values differ.",
    )
    payload, _ = _assess(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE)], [conflict])
    serialized = str(payload.model_dump()).lower()
    for forbidden in (
        "ground_truth", "expected_risk", "is_tampered", "raw_details", "raw_ocr_text",
        "document_image", "api_key", "secret ocr", "secret-a", "secret-b", "value_a", "value_b",
    ):
        assert forbidden not in serialized
    assert payload.evidence_signals[0].title == "Check"
    assert payload.conflicts[0].field_name == "document_number"


def test_deterministic_provider_returns_structured_advisory_output():
    _, result = _assess(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE, "Visual anomaly")])
    assert result.advisory is True
    assert result.provider == "deterministic-local"
    assert result.key_risk_factors and "suspicious" in result.reasoning_summary.lower()
    assert result.human_decision_required is True


def test_missing_evidence_is_uncertain_not_negative():
    _, result = _assess(RiskLevel.GREY, [_signal(EvidenceState.MISSING, "Secondary document")], uncertainty=0.8)
    assert not result.key_risk_factors
    assert "missing" in result.uncertainty_factors[0].lower()


def test_deterministic_repeatability():
    payload, first = _assess(RiskLevel.AMBER, [_signal(EvidenceState.NEGATIVE, "Visual anomaly")])
    assert first.model_dump() == DeterministicAIRiskReasoningAdapter().assess(payload).model_dump()


def test_disabled_mode_does_not_add_advisory_or_change_result():
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_001_GENUINE")
    assert sample
    default = run_screening_pipeline(sample, enable_evidence_fusion=True, enable_officer_review=True)
    disabled = run_screening_pipeline(
        sample, enable_evidence_fusion=True, enable_officer_review=True, enable_ai_risk_reasoning=False,
    )
    assert default.ai_risk_reasoning is None and disabled.ai_risk_reasoning is None
    assert "ai_risk_reasoning" not in default.model_dump()
    assert (default.risk_level, default.risk_score, default.uncertainty_score) == (
        disabled.risk_level, disabled.risk_score, disabled.uncertainty_score,
    )


def test_enabled_mode_is_additive_and_preserves_deterministic_decision():
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_002_TAMPERED")
    assert sample
    baseline = run_screening_pipeline(sample, enable_cross_document_consistency=True, enable_evidence_fusion=True)
    advised = run_screening_pipeline(
        sample, enable_cross_document_consistency=True, enable_evidence_fusion=True, enable_ai_risk_reasoning=True,
    )
    assert advised.ai_risk_reasoning and advised.ai_risk_reasoning.human_decision_required is True
    assert (baseline.risk_level, baseline.risk_score, baseline.uncertainty_score) == (
        advised.risk_level, advised.risk_score, advised.uncertainty_score,
    )
    assert [item.model_dump() for item in baseline.evidence_signals] == [item.model_dump() for item in advised.evidence_signals]
    assert [item.model_dump() for item in baseline.conflicts] == [item.model_dump() for item in advised.conflicts]


def test_provider_failure_returns_unavailable_advisory_without_changing_screening():
    class FailingAdapter:
        def assess(self, payload):
            raise RuntimeError("provider unavailable")

    sample = DatasetRegistry.get("synthetic").get_sample("CASE_002_TAMPERED")
    assert sample
    baseline = run_screening_pipeline(sample)
    original_factory = pipeline_module.get_ai_risk_reasoning_adapter
    pipeline_module.get_ai_risk_reasoning_adapter = lambda: FailingAdapter()
    try:
        advised = run_screening_pipeline(sample, enable_ai_risk_reasoning=True)
    finally:
        pipeline_module.get_ai_risk_reasoning_adapter = original_factory
    assert advised.ai_risk_reasoning and advised.ai_risk_reasoning.provider == "unavailable"
    assert advised.ai_risk_reasoning.human_decision_required is True
    assert (baseline.risk_level, baseline.risk_score, baseline.uncertainty_score) == (
        advised.risk_level, advised.risk_score, advised.uncertainty_score,
    )


def test_only_local_provider_is_available():
    assert isinstance(get_ai_risk_reasoning_adapter(), DeterministicAIRiskReasoningAdapter)
    try:
        get_ai_risk_reasoning_adapter("unsupported")
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported providers must not be selected")
