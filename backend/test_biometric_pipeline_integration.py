"""Focused M8 opt-in pipeline tests."""

import app.data.synthetic_adapter
from app.data.base import DatasetRegistry
from app.data.models import EvidenceState, RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_biometric_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "BIOMETRIC" for signal in result.evidence_signals)


def test_opt_in_biometric_adds_zero_risk_fallback_evidence():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_biometric_verification=True)
    signal = next(signal for signal in result.evidence_signals if signal.source == "BIOMETRIC")
    assert result.risk_level == RiskLevel.GREEN
    assert signal.evidence_state == EvidenceState.POSITIVE
    assert signal.contribution == 0.0
    assert signal.raw_details["demo_only"] is True


def test_opt_in_biometric_preserves_deterministic_outcomes():
    expected = {
        "CASE_001_GENUINE": RiskLevel.GREEN,
        "CASE_002_TAMPERED": RiskLevel.RED,
        "CASE_003_UNCERTAIN": RiskLevel.GREY,
    }
    for sample_id, risk_level in expected.items():
        result = run_screening_pipeline(_sample(sample_id), enable_biometric_verification=True)
        signal = next(signal for signal in result.evidence_signals if signal.source == "BIOMETRIC")
        assert result.risk_level == risk_level
        assert signal.contribution == 0.0


if __name__ == "__main__":
    test_biometric_is_disabled_by_default()
    test_opt_in_biometric_adds_zero_risk_fallback_evidence()
    test_opt_in_biometric_preserves_deterministic_outcomes()
    print("[SUCCESS] Biometric pipeline integration tests passed.")
