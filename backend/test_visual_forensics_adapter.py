"""Focused M7 tests using only synthetic fixtures and temporary images."""

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from app.data.models import CanonicalDocumentSample, EvidenceState
from app.services import visual_forensics_adapter
from app.services.visual_forensics_adapter import (
    PillowVisualForensicsAdapter,
    extract_visual_forensics_evidence,
)


ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "datasets" / "synthetic" / "genuine" / "passport_001.png"


def test_decodable_synthetic_fixture_has_computed_metrics():
    result = PillowVisualForensicsAdapter().analyze(FIXTURE)
    assert result.metadata["image_decodable"] is True
    assert result.metadata["width"] == 1200
    assert result.metadata["height"] == 760
    assert result.metadata["anomaly_regions"] == []
    assert result.metadata["compression_analysis"]["ela_available"] is False


def test_missing_and_malformed_inputs_fail_safely():
    adapter = PillowVisualForensicsAdapter()
    missing = adapter.analyze("missing-image.png")
    assert missing.evidence_state == EvidenceState.MISSING
    assert missing.metadata["real_analysis_used"] is False
    assert missing.metadata["fallback_used"] is False
    assert missing.metadata["unavailable_mode"] is True
    with TemporaryDirectory() as directory:
        malformed = Path(directory) / "not-an-image.png"
        malformed.write_bytes(b"not an image")
        malformed_result = adapter.analyze(malformed)
        assert malformed_result.evidence_state == EvidenceState.UNAVAILABLE
        assert malformed_result.metadata["real_analysis_used"] is False
        assert malformed_result.metadata["fallback_used"] is False
        assert malformed_result.metadata["unavailable_mode"] is True


def test_missing_pillow_capability_fails_safely():
    original_image = visual_forensics_adapter.Image
    try:
        visual_forensics_adapter.Image = None
        result = PillowVisualForensicsAdapter().analyze(FIXTURE)
    finally:
        visual_forensics_adapter.Image = original_image

    assert result.evidence_state == EvidenceState.UNAVAILABLE
    assert result.metadata["reason"] == "pillow_not_available"
    assert result.metadata["real_analysis_used"] is False
    assert result.metadata["fallback_used"] is False
    assert result.metadata["unavailable_mode"] is True


def test_low_quality_and_jpeg_recompression_metrics_are_computed():
    with TemporaryDirectory() as directory:
        directory_path = Path(directory)
        low_quality = directory_path / "low.png"
        Image.new("RGB", (32, 32), color=(128, 128, 128)).save(low_quality)
        low_result = PillowVisualForensicsAdapter().analyze(low_quality)
        assert low_result.evidence_state == EvidenceState.UNRELIABLE

        jpeg = directory_path / "synthetic.jpg"
        image = Image.new("RGB", (400, 300), color="white")
        ImageDraw.Draw(image).rectangle((80, 80, 320, 220), fill="black")
        image.save(jpeg, format="JPEG", quality=70)
        jpeg_result = PillowVisualForensicsAdapter().analyze(jpeg)
        compression = jpeg_result.metadata["compression_analysis"]
        assert compression["ela_available"] is True
        assert "ela_mean_difference" in compression


def test_evidence_is_supporting_and_zero_risk_for_unavailable_input():
    sample = CanonicalDocumentSample(sample_id="MISSING_VISUAL", source_dataset="synthetic", document_image="missing-image.png")
    signal = extract_visual_forensics_evidence(sample)[0]
    assert signal.source == "VISUAL_FORENSICS"
    assert signal.category.value == "VISUAL_FORENSIC"
    assert signal.evidence_state == EvidenceState.MISSING
    assert signal.contribution == 0.0
    assert signal.limitation


if __name__ == "__main__":
    test_decodable_synthetic_fixture_has_computed_metrics()
    test_missing_and_malformed_inputs_fail_safely()
    test_missing_pillow_capability_fails_safely()
    test_low_quality_and_jpeg_recompression_metrics_are_computed()
    test_evidence_is_supporting_and_zero_risk_for_unavailable_input()
    print("[SUCCESS] Visual-forensics adapter tests passed.")
