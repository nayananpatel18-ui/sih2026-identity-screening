"""Focused M7 opt-in pipeline tests."""

import app.data.synthetic_adapter
from app.data.base import DatasetRegistry
from app.data.models import RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_visual_forensics_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "VISUAL_FORENSICS" for signal in result.evidence_signals)


def test_opt_in_visual_forensics_adds_supporting_evidence():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_visual_forensics=True)
    signal = next(signal for signal in result.evidence_signals if signal.source == "VISUAL_FORENSICS")
    assert result.risk_level == RiskLevel.GREEN
    assert signal.contribution == 0.0
    assert signal.raw_details["real_analysis_used"] is True
    assert signal.raw_details["anomaly_regions"] == []


def test_all_opt_in_adapters_remain_compatible():
    result = run_screening_pipeline(
        _sample("CASE_001_GENUINE"),
        enable_ocr=True,
        enable_mrz=True,
        enable_visual_forensics=True,
    )
    assert result.risk_level == RiskLevel.GREEN
    assert {"OCR", "MRZ", "VISUAL_FORENSICS"}.issubset({signal.source for signal in result.evidence_signals})


def test_visual_forensics_preserves_all_case_outcomes():
    expected = {
        "CASE_001_GENUINE": RiskLevel.GREEN,
        "CASE_002_TAMPERED": RiskLevel.RED,
        "CASE_003_UNCERTAIN": RiskLevel.GREY,
    }
    for sample_id, risk_level in expected.items():
        assert run_screening_pipeline(_sample(sample_id), enable_visual_forensics=True).risk_level == risk_level


if __name__ == "__main__":
    test_visual_forensics_is_disabled_by_default()
    test_opt_in_visual_forensics_adds_supporting_evidence()
    test_all_opt_in_adapters_remain_compatible()
    test_visual_forensics_preserves_all_case_outcomes()
    print("[SUCCESS] Visual-forensics pipeline integration tests passed.")
