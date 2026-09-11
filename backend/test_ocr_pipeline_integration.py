"""Focused M5.2 verification for opt-in OCR pipeline evidence."""

import app.data.synthetic_adapter  # Registers the synthetic adapter.
from app.data.base import DatasetRegistry
from app.data.models import EvidenceState, RiskLevel
from app.services.pipeline import run_screening_pipeline


def _sample(sample_id: str):
    sample = DatasetRegistry.get("synthetic").get_sample(sample_id)
    assert sample
    return sample


def test_ocr_is_disabled_by_default():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"))
    assert not any(signal.source == "OCR" for signal in result.evidence_signals)
    assert result.risk_level == RiskLevel.GREEN


def test_opt_in_ocr_adds_synthetic_provenance_without_risk_change():
    result = run_screening_pipeline(_sample("CASE_001_GENUINE"), enable_ocr=True)
    ocr_signals = [signal for signal in result.evidence_signals if signal.source == "OCR"]

    assert result.risk_level == RiskLevel.GREEN
    assert result.risk_score == 0.0
    assert ocr_signals
    extracted = next(signal for signal in ocr_signals if signal.evidence_state == EvidenceState.POSITIVE)
    assert extracted.raw_details["ocr_metadata"]["engine"] == "synthetic_fixture_fallback"
    assert extracted.raw_details["ocr_metadata"]["fallback_used"] is True
    assert extracted.raw_details["ocr_metadata"]["demo_only"] is True
    assert extracted.raw_details["ocr_metadata"]["real_engine_status"] == "unavailable"
    assert extracted.raw_details["extracted_fields"]["full_name"] == "RAJESH KUMAR SHARMA"
    assert all(signal.contribution == 0.0 for signal in ocr_signals)


def test_unreliable_ocr_does_not_become_negative_evidence():
    result = run_screening_pipeline(_sample("CASE_003_UNCERTAIN"), enable_ocr=True)
    ocr_signals = [signal for signal in result.evidence_signals if signal.source == "OCR"]

    assert result.risk_level == RiskLevel.GREY
    assert result.risk_score == 0.0
    assert any(signal.evidence_state == EvidenceState.UNRELIABLE for signal in ocr_signals)
    assert not any(signal.evidence_state == EvidenceState.NEGATIVE for signal in ocr_signals)
    assert all(signal.contribution == 0.0 for signal in ocr_signals)


if __name__ == "__main__":
    test_ocr_is_disabled_by_default()
    test_opt_in_ocr_adds_synthetic_provenance_without_risk_change()
    test_unreliable_ocr_does_not_become_negative_evidence()
    print("[SUCCESS] OCR pipeline integration tests passed.")
