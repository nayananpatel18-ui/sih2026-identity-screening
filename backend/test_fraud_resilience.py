"""Focused deterministic M12 resilience-lab tests using synthetic values only."""

import app.data.synthetic_adapter

from app.data.base import DatasetRegistry
from app.data.models import EvidenceState, RiskLevel
from app.services.fraud_resilience import FraudResilienceService, ResponseCategory
from app.services.pipeline import run_screening_pipeline


def _evaluate(scenario_id):
    return FraudResilienceService().evaluate(scenario_id)


def test_baseline_genuine_has_no_significant_lab_signal():
    result = _evaluate("M12_BASELINE_GENUINE")
    assert result.observed_risk_level == RiskLevel.GREEN
    assert result.response_category == ResponseCategory.NO_SIGNIFICANT_SIGNAL
    assert {"M5_OCR", "M6_MRZ_STRUCTURAL_VALIDATION", "M7_VISUAL_FORENSICS", "M8_SYNTHETIC_AVATAR_PROXY", "M10_EVIDENCE_FUSION", "M11_OFFICER_REVIEW"}.issubset(result.components_exercised)


def test_field_alteration_produces_a_bounded_suspicious_signal():
    result = _evaluate("M12_FIELD_ALTERATION")
    assert result.observed_risk_level == RiskLevel.RED
    assert result.response_category == ResponseCategory.DETECTED_CONFLICT
    assert "SIG_MRZ_RUNTIME_CASE_002_TAMPERED" in result.detected_signals
    assert "M6_MRZ_STRUCTURAL_VALIDATION" in result.components_exercised


def test_cross_document_mismatch_surfaces_actual_conflict():
    result = _evaluate("M12_CROSS_DOCUMENT_MISMATCH")
    assert result.response_category == ResponseCategory.DETECTED_CONFLICT
    assert result.detected_conflicts
    assert "M9_CROSS_DOCUMENT_CONSISTENCY" in result.components_exercised


def test_biometric_proxy_inconsistency_is_not_face_recognition():
    result = _evaluate("M12_BIOMETRIC_PROXY_INCONSISTENCY")
    scenario = next(item for item in FraudResilienceService().list_scenarios() if item["scenario_id"] == "M12_BIOMETRIC_PROXY_INCONSISTENCY")
    assert result.response_category == ResponseCategory.UNCERTAINTY_ESCALATED
    assert result.evidence_coverage["unreliable_count"] == 1
    assert "M8_SYNTHETIC_AVATAR_PROXY" in result.components_exercised
    assert "not face recognition" in scenario["description"].lower()


def test_low_quality_escalates_uncertainty_to_grey():
    result = _evaluate("M12_LOW_QUALITY")
    assert result.observed_risk_level == RiskLevel.GREY
    assert result.response_category == ResponseCategory.UNCERTAINTY_ESCALATED
    assert {"M5_OCR", "M6_MRZ_STRUCTURAL_VALIDATION", "M7_VISUAL_FORENSICS"}.issubset(result.components_exercised)


def test_missing_evidence_is_coverage_limitation_not_negative_evidence():
    result = _evaluate("M12_MISSING_EVIDENCE")
    assert result.response_category == ResponseCategory.INSUFFICIENT_EVIDENCE
    assert result.evidence_coverage["missing_count"] == 1
    assert result.observed_risk_score == 0.0


def test_unavailable_analysis_is_not_negative_evidence():
    result = _evaluate("M12_UNAVAILABLE_ANALYSIS")
    assert result.response_category == ResponseCategory.ANALYSIS_UNAVAILABLE
    assert result.evidence_coverage["unavailable_count"] == 1
    assert result.observed_risk_score == 0.0


def test_unreliable_evidence_is_not_a_contradiction():
    result = _evaluate("M12_UNRELIABLE_EVIDENCE")
    assert result.response_category == ResponseCategory.UNCERTAINTY_ESCALATED
    assert result.detected_conflicts == []
    assert result.observed_risk_score == 0.0


def test_multiple_independent_suspicious_signals_reach_red():
    result = _evaluate("M12_MULTI_SIGNAL")
    assert result.observed_risk_level == RiskLevel.RED
    assert len(result.detected_signals) >= 2
    assert {"M5_OCR", "M6_MRZ_STRUCTURAL_VALIDATION", "M7_VISUAL_FORENSICS", "M8_SYNTHETIC_AVATAR_PROXY", "M9_CROSS_DOCUMENT_CONSISTENCY", "M10_EVIDENCE_FUSION", "M11_OFFICER_REVIEW"}.issubset(result.components_exercised)


def test_same_scenario_is_deterministic():
    assert _evaluate("M12_MULTI_SIGNAL").to_dict() == _evaluate("M12_MULTI_SIGNAL").to_dict()


def test_lab_and_officer_outputs_do_not_leak_evaluation_metadata():
    lab_output = _evaluate("M12_FIELD_ALTERATION").to_dict()
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_001_GENUINE")
    officer_output = run_screening_pipeline(sample, enable_officer_review=True).officer_review.model_dump()
    assert "expected_behavior" not in str(lab_output).lower()
    assert "ground_truth" not in str(lab_output).lower()
    assert "ground_truth" not in str(officer_output).lower()
    assert "m12_" not in str(officer_output).lower()


def test_m12_is_disabled_for_normal_pipeline_runs():
    sample = DatasetRegistry.get("synthetic").get_sample("CASE_001_GENUINE")
    result = run_screening_pipeline(sample, enable_evidence_fusion=True, enable_officer_review=True)
    assert result.risk_level == RiskLevel.GREEN
    assert not any(signal.signal_id.startswith("SIG_M12_") for signal in result.evidence_signals)
    assert not any(signal.evidence_state == EvidenceState.NEGATIVE for signal in result.evidence_signals)


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_"):
            function()
    print("[SUCCESS] Fraud resilience tests passed.")
