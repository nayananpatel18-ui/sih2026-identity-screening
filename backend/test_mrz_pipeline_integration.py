"""Focused M6 tests for opt-in MRZ pipeline evidence."""

import app.data.synthetic_adapter  # Registers synthetic samples.
from app.data.base import DatasetRegistry
from app.data.models import EvidenceState, RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_mrz_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "MRZ" for signal in result.evidence_signals)


def test_opt_in_mrz_adds_structural_evidence_without_risk_reweighting():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_mrz=True)
    signals = [signal for signal in result.evidence_signals if signal.source == "MRZ"]
    assert result.risk_level == RiskLevel.GREEN
    assert signals and signals[0].evidence_state == EvidenceState.POSITIVE
    assert all(signals[0].raw_details["check_digits"].values())
    assert signals[0].contribution == 0.0


def test_incomplete_mrz_is_unreliable_not_negative():
    result = run_screening_pipeline(_sample("CASE_003_UNCERTAIN"), enable_mrz=True)
    signal = next(signal for signal in result.evidence_signals if signal.source == "MRZ")
    assert result.risk_level == RiskLevel.GREY
    assert signal.evidence_state == EvidenceState.UNRELIABLE
    assert signal.contribution == 0.0


def test_mrz_enabled_preserves_all_case_outcomes():
    expected = {
        "CASE_001_GENUINE": RiskLevel.GREEN,
        "CASE_002_TAMPERED": RiskLevel.RED,
        "CASE_003_UNCERTAIN": RiskLevel.GREY,
    }
    for sample_id, risk_level in expected.items():
        result = run_screening_pipeline(_sample(sample_id), enable_mrz=True)
        assert result.risk_level == risk_level


if __name__ == "__main__":
    test_mrz_is_disabled_by_default()
    test_opt_in_mrz_adds_structural_evidence_without_risk_reweighting()
    test_incomplete_mrz_is_unreliable_not_negative()
    test_mrz_enabled_preserves_all_case_outcomes()
    print("[SUCCESS] MRZ pipeline integration tests passed.")
