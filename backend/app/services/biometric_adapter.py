"""M8 biometric-verification boundary for synthetic development fixtures only.

No face-recognition engine is bundled with this prototype.  The Pillow fallback
therefore checks only the visual consistency of the clearly labelled synthetic
avatar fixtures; it is not facial recognition and never asserts identity.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Protocol

try:
    from PIL import Image, ImageStat, UnidentifiedImageError
except ImportError:  # Pillow is an optional local capability.
    Image = ImageStat = None  # type: ignore[assignment]
    UnidentifiedImageError = OSError

from app.data.models import (
    BiometricMatchResult,
    CanonicalDocumentSample,
    EvidenceSignal,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
)


@dataclass
class BiometricVerificationResult:
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_state: EvidenceState = EvidenceState.UNAVAILABLE
    comparison_result: BiometricMatchResult = BiometricMatchResult.UNAVAILABLE
    confidence: float = 0.0
    limitation: str = (
        "No face-recognition model is installed. This demo-only synthetic-avatar "
        "proxy does not detect faces, verify identity, or prove a match or mismatch."
    )


class BiometricVerificationAdapter(Protocol):
    def compare(
        self,
        person_image: str | Path | None,
        document_image: str | Path | None,
        *,
        document_quality_sufficient: bool = True,
    ) -> BiometricVerificationResult:
        """Compare a person image with a document portrait when an engine is available."""


class PillowSyntheticAvatarBiometricAdapter:
    """Safe development fallback for the repository's labelled abstract avatars."""

    engine_name = "pillow_synthetic_avatar_proxy"

    def compare(
        self,
        person_image: str | Path | None,
        document_image: str | Path | None,
        *,
        document_quality_sufficient: bool = True,
    ) -> BiometricVerificationResult:
        if Image is None:
            return self._result(
                EvidenceState.UNAVAILABLE,
                BiometricMatchResult.UNAVAILABLE,
                0.0,
                {"reason": "pillow_not_available"},
                unavailable_mode=True,
            )
        if not person_image:
            return self._result(EvidenceState.MISSING, BiometricMatchResult.UNAVAILABLE, 0.0, {"reason": "person_image_missing"}, unavailable_mode=True)
        if not document_image:
            return self._result(EvidenceState.MISSING, BiometricMatchResult.UNAVAILABLE, 0.0, {"reason": "document_image_missing"}, unavailable_mode=True)

        person = self._load_image(person_image)
        document = self._load_image(document_image)
        if person is None or document is None:
            missing_side = "person_image" if person is None else "document_image"
            return self._result(
                EvidenceState.UNAVAILABLE,
                BiometricMatchResult.UNAVAILABLE,
                0.0,
                {"reason": f"{missing_side}_decode_failed"},
                unavailable_mode=True,
            )

        person_quality = self._quality(person)
        document_quality = self._quality(document)
        quality_metadata = {"person": person_quality, "document": document_quality}
        if not document_quality_sufficient or not person_quality["usable"] or not document_quality["usable"]:
            return self._result(
                EvidenceState.UNRELIABLE,
                BiometricMatchResult.INCONCLUSIVE,
                0.0,
                {"reason": "insufficient_image_quality", "image_quality": quality_metadata, "face_detection": "not_available_without_face_engine"},
            )

        # This recognizes only the simple color/layout convention of the project's
        # abstract, visibly labelled demo fixtures. It is deliberately not a face detector.
        person_marker = person.getpixel((person.width // 2, int(person.height * 0.35)))
        document_marker = document.getpixel((10, 10))
        if not self._is_synthetic_marker(person_marker) or not self._is_synthetic_marker(document_marker):
            return self._result(
                EvidenceState.UNAVAILABLE,
                BiometricMatchResult.UNAVAILABLE,
                0.0,
                {"reason": "no_usable_synthetic_avatar_region", "image_quality": quality_metadata, "face_detection": "not_available_without_face_engine"},
                unavailable_mode=True,
            )

        distance = round(sum((left - right) ** 2 for left, right in zip(person_marker, document_marker)) ** 0.5, 4)
        similarity = round(max(0.0, 1.0 - distance / 441.6729559), 4)
        if distance > 85:
            return self._result(
                EvidenceState.UNRELIABLE,
                BiometricMatchResult.INCONCLUSIVE,
                0.0,
                {
                    "reason": "synthetic_proxy_inconsistent",
                    "image_quality": quality_metadata,
                    "face_detection": "not_available_without_face_engine",
                    "comparison_score": similarity,
                    "comparison_metric": "synthetic_theme_color_similarity",
                    "threshold": 85,
                },
            )

        return self._result(
            EvidenceState.POSITIVE,
            BiometricMatchResult.MATCH,
            0.30,
            {
                "image_quality": quality_metadata,
                "face_detection": "not_available_without_face_engine",
                "comparison_score": similarity,
                "comparison_metric": "synthetic_theme_color_similarity",
                "threshold": 85,
                "comparison_note": "A synthetic-fixture layout proxy was consistent; this is not a facial similarity score.",
            },
        )

    @staticmethod
    def _resolve_path(image_path: str | Path) -> Path:
        path = Path(image_path)
        if path.is_file():
            return path
        return Path(__file__).resolve().parents[3] / path

    def _load_image(self, image_path: str | Path):
        path = self._resolve_path(image_path)
        if not path.is_file():
            return None
        try:
            with Image.open(path) as source:
                source.load()
                return source.convert("RGB")
        except (UnidentifiedImageError, OSError):
            return None

    @staticmethod
    def _quality(image: Any) -> Dict[str, Any]:
        luminance = image.convert("L")
        contrast = round(ImageStat.Stat(luminance).var[0] ** 0.5, 4)
        usable = image.width >= 160 and image.height >= 160 and contrast >= 8
        return {"width": image.width, "height": image.height, "contrast_standard_deviation": contrast, "usable": usable}

    @staticmethod
    def _is_synthetic_marker(pixel: tuple[int, int, int]) -> bool:
        return max(pixel) - min(pixel) >= 40 and max(pixel) >= 80

    def _result(
        self,
        evidence_state: EvidenceState,
        comparison_result: BiometricMatchResult,
        confidence: float,
        details: Dict[str, Any],
        *,
        unavailable_mode: bool = False,
    ) -> BiometricVerificationResult:
        return BiometricVerificationResult(
            metadata={
                "source": "BIOMETRIC",
                "engine": self.engine_name,
                "real_engine_available": False,
                "fallback_used": True,
                "demo_only": True,
                "unavailable_mode": unavailable_mode,
                **details,
            },
            evidence_state=evidence_state,
            comparison_result=comparison_result,
            confidence=confidence,
        )


def extract_biometric_evidence(
    sample: CanonicalDocumentSample,
    adapter: BiometricVerificationAdapter | None = None,
) -> List[EvidenceSignal]:
    """Map M8 adapter output to isolated, zero-risk supporting evidence."""
    result = (adapter or PillowSyntheticAvatarBiometricAdapter()).compare(
        sample.person_image,
        sample.document_image,
        document_quality_sufficient=sample.quality_metadata.is_sufficient_quality,
    )
    if result.evidence_state == EvidenceState.POSITIVE:
        title = "Synthetic Avatar Consistency Available"
        description = "A demo-only synthetic-avatar layout proxy was consistent. This is not facial identity verification."
        severity = SignalSeverity.INFO
    elif result.evidence_state == EvidenceState.UNRELIABLE:
        title = "Biometric Comparison Inconclusive"
        description = "Image quality or synthetic-proxy consistency was insufficient for comparison. This is not a fraud signal."
        severity = SignalSeverity.INFO
    elif result.evidence_state == EvidenceState.MISSING:
        title = "Biometric Comparison Input Missing"
        description = "A required comparison image was not provided. Missing input is not a fraud signal."
        severity = SignalSeverity.INFO
    else:
        title = "Biometric Comparison Unavailable"
        description = "No usable biometric engine or synthetic comparison input was available. This is not a fraud signal."
        severity = SignalSeverity.INFO

    return [EvidenceSignal(
        signal_id=f"SIG_BIOMETRIC_RUNTIME_{sample.sample_id}",
        source="BIOMETRIC",
        category=SignalCategory.BIOMETRIC_VERIFICATION,
        evidence_state=result.evidence_state,
        severity=severity,
        title=title,
        description=description,
        confidence=result.confidence,
        contribution=0.0,
        limitation=result.limitation,
        raw_details={**result.metadata, "comparison_result": result.comparison_result.value},
    )]
