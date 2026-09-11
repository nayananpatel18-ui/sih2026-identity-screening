"""Focused M10 opt-in pipeline integration tests."""

import app.data.synthetic_adapter
from app.data.base import DatasetRegistry
from app.data.models import RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_evidence_fusion_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "EVIDENCE_FUSION" for signal in result.evidence_signals)


def test_opt_in_evidence_fusion_adds_zero_risk_summary():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_evidence_fusion=True)
    signal = next(signal for signal in result.evidence_signals if signal.source == "EVIDENCE_FUSION")
    assert result.risk_level == RiskLevel.GREEN
    assert signal.contribution == 0.0
    assert signal.raw_details["coverage"]["signal_count"] > 0
    assert "ground_truth" not in str(signal.raw_details).lower()


def test_opt_in_fusion_preserves_deterministic_cases_and_m9_conflicts():
    expected = {
        "CASE_001_GENUINE": RiskLevel.GREEN,
        "CASE_002_TAMPERED": RiskLevel.RED,
        "CASE_003_UNCERTAIN": RiskLevel.GREY,
    }
    for sample_id, level in expected.items():
        result = run_screening_pipeline(
            _sample(sample_id),
            enable_cross_document_consistency=True,
            enable_evidence_fusion=True,
        )
        assert result.risk_level == level
        summary = next(signal for signal in result.evidence_signals if signal.source == "EVIDENCE_FUSION")
        assert summary.raw_details["risk_level"] == level.value


if __name__ == "__main__":
    test_evidence_fusion_is_disabled_by_default()
    test_opt_in_evidence_fusion_adds_zero_risk_summary()
    test_opt_in_fusion_preserves_deterministic_cases_and_m9_conflicts()
    print("[SUCCESS] Evidence fusion pipeline integration tests passed.")
