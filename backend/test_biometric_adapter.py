"""Focused M8 tests for the clearly labelled synthetic-avatar fallback only."""

from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from app.data.models import CanonicalDocumentSample, EvidenceState
from app.services.biometric_adapter import PillowSyntheticAvatarBiometricAdapter, extract_biometric_evidence


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "datasets" / "synthetic"
PERSON = FIXTURES / "genuine" / "person_001.png"
DOCUMENT = FIXTURES / "genuine" / "passport_001.png"


def test_synthetic_pair_produces_structured_demo_only_result():
    result = PillowSyntheticAvatarBiometricAdapter().compare(PERSON, DOCUMENT)
    assert result.evidence_state == EvidenceState.POSITIVE
    assert result.metadata["engine"] == "pillow_synthetic_avatar_proxy"
    assert result.metadata["real_engine_available"] is False
    assert result.metadata["fallback_used"] is True
    assert result.metadata["demo_only"] is True
    assert "comparison_score" in result.metadata
    assert result.metadata["face_detection"] == "not_available_without_face_engine"


def test_missing_inputs_are_safe_and_not_negative():
    adapter = PillowSyntheticAvatarBiometricAdapter()
    missing_person = adapter.compare(None, DOCUMENT)
    missing_document = adapter.compare(PERSON, None)
    assert missing_person.evidence_state == EvidenceState.MISSING
    assert missing_document.evidence_state == EvidenceState.MISSING


def test_low_quality_or_inconsistent_proxy_is_not_negative():
    adapter = PillowSyntheticAvatarBiometricAdapter()
    with TemporaryDirectory() as directory:
        poor_person = Path(directory) / "poor.png"
        Image.new("RGB", (32, 32), color=(128, 128, 128)).save(poor_person)
        poor_result = adapter.compare(poor_person, DOCUMENT)
    inconsistent_result = adapter.compare(FIXTURES / "tampered" / "person_002.png", DOCUMENT)
    assert poor_result.evidence_state == EvidenceState.UNRELIABLE
    assert inconsistent_result.evidence_state == EvidenceState.UNRELIABLE


def test_biometric_evidence_is_zero_risk_and_labelled_as_fallback():
    sample = CanonicalDocumentSample(
        sample_id="BIOMETRIC_TEST",
        source_dataset="synthetic",
        document_image=str(DOCUMENT),
        person_image=str(PERSON),
    )
    signal = extract_biometric_evidence(sample)[0]
    assert signal.source == "BIOMETRIC"
    assert signal.contribution == 0.0
    assert signal.raw_details["fallback_used"] is True
    assert signal.limitation


if __name__ == "__main__":
    test_synthetic_pair_produces_structured_demo_only_result()
    test_missing_inputs_are_safe_and_not_negative()
    test_low_quality_or_inconsistent_proxy_is_not_negative()
    test_biometric_evidence_is_zero_risk_and_labelled_as_fallback()
    print("[SUCCESS] Biometric adapter tests passed.")
