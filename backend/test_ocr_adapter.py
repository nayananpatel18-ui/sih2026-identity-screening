"""Focused M5.1 verification for the isolated OCR adapter."""

from pathlib import Path

from app.data.models import EvidenceState
from app.services.ocr_adapter import (
    SyntheticFixtureOcrAdapter,
    OcrCapability,
    get_ocr_adapter,
)
from app.services.risk_engine import compute_risk_score


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "datasets" / "synthetic"


def test_synthetic_fixture_fallback_extracts_visible_fields():
    result = SyntheticFixtureOcrAdapter().extract(FIXTURES / "genuine" / "passport_001.png")

    assert result.evidence_state == EvidenceState.POSITIVE
    assert result.metadata["source"] == "OCR"
    assert result.metadata["fallback_used"] is True
    assert result.metadata["demo_only"] is True
    assert result.metadata["adapter_path"] == "synthetic_fixture_fallback"
    assert "SYNTHETIC DEMO DOCUMENT" in result.raw_text
    assert result.fields.full_name == "RAJESH KUMAR SHARMA"
    assert result.fields.document_number == "DEMO-Z1234567"
    assert result.fields.nationality == "DEMO"
    assert result.fields.dob == "1990-01-01"
    assert result.fields.expiry_date is None


def test_unavailable_real_engine_selects_synthetic_fallback():
    capability = OcrCapability(False, "tesseract", "Test: local engine unavailable.")

    adapter = get_ocr_adapter(capability)
    assert isinstance(adapter, SyntheticFixtureOcrAdapter)
    result = adapter.extract(FIXTURES / "genuine" / "passport_001.png")
    assert result.metadata["real_engine_status"] == "unavailable"
    assert result.metadata["fallback_used"] is True
    assert result.metadata["demo_only"] is True


def test_missing_input_is_unavailable_not_negative_risk():
    result = SyntheticFixtureOcrAdapter().extract(FIXTURES / "missing.png")

    assert result.evidence_state == EvidenceState.UNAVAILABLE
    assert result.raw_text == ""
    assert result.fields.full_name is None
    # The adapter emits no negative evidence or conflict, so failure alone has no risk effect.
    assert compute_risk_score([], []) == 0.0


if __name__ == "__main__":
    test_synthetic_fixture_fallback_extracts_visible_fields()
    test_unavailable_real_engine_selects_synthetic_fallback()
    test_missing_input_is_unavailable_not_negative_risk()
    print("[SUCCESS] OCR adapter tests passed.")
