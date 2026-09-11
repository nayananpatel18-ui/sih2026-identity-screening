"""Small deterministic visual-forensics adapter for M7 supporting evidence only.

The adapter computes basic Pillow-based image quality metrics and an optional
JPEG recompression (ELA-style) metric.  Neither result authenticates a document
or proves tampering.
"""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Protocol

try:
    from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError
except ImportError:  # Pillow is an optional local capability for this adapter.
    Image = ImageChops = ImageFilter = ImageOps = ImageStat = None  # type: ignore[assignment]
    UnidentifiedImageError = OSError

from app.data.models import (
    CanonicalDocumentSample,
    EvidenceSignal,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
)


@dataclass
class VisualForensicsResult:
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_state: EvidenceState = EvidenceState.UNAVAILABLE
    confidence: float = 0.0
    limitation: str = "Visual analysis provides supporting information only and cannot prove document authenticity or tampering."


class VisualForensicsAdapter(Protocol):
    def analyze(self, image_path: str | Path) -> VisualForensicsResult:
        """Analyze a local document image without persisting its pixels or bytes."""


class PillowVisualForensicsAdapter:
    """Pillow-only quality and JPEG recompression metrics with no cloud or GPU dependency."""

    engine_name = "pillow_basic_visual_forensics"

    def analyze(self, image_path: str | Path) -> VisualForensicsResult:
        if Image is None:
            return self._result(
                EvidenceState.UNAVAILABLE,
                0.0,
                {"reason": "pillow_not_available"},
                real_analysis_used=False,
                unavailable_mode=True,
            )

        path = Path(image_path)
        if not path.is_file():
            path = Path(__file__).resolve().parents[3] / path
        if not path.is_file():
            return self._result(
                EvidenceState.MISSING,
                0.0,
                {"reason": "image_path_missing"},
                real_analysis_used=False,
                unavailable_mode=True,
            )

        try:
            with Image.open(path) as source:
                source.load()
                image = source.convert("RGB")
                image_format = source.format or "UNKNOWN"
        except (UnidentifiedImageError, OSError):
            return self._result(
                EvidenceState.UNAVAILABLE,
                0.0,
                {"reason": "image_decode_failed"},
                real_analysis_used=False,
                unavailable_mode=True,
            )

        width, height = image.size
        grayscale = ImageOps.grayscale(image)
        brightness = round(ImageStat.Stat(grayscale).mean[0], 4)
        contrast = round(ImageStat.Stat(grayscale).var[0] ** 0.5, 4)
        edge_variance = round(ImageStat.Stat(grayscale.filter(ImageFilter.FIND_EDGES)).var[0], 4)
        quality_reasons: List[str] = []
        if width < 300 or height < 300:
            quality_reasons.append("low_resolution")
        if brightness < 25 or brightness > 230:
            quality_reasons.append("extreme_brightness")
        if contrast < 12:
            quality_reasons.append("low_contrast")
        if edge_variance < 100:
            quality_reasons.append("low_edge_detail")

        compression = self._compression_metadata(image, image_format)
        state = EvidenceState.UNRELIABLE if quality_reasons else EvidenceState.POSITIVE
        confidence = 0.25 if quality_reasons else 0.70
        return self._result(state, confidence, {
            "image_decodable": True,
            "width": width,
            "height": height,
            "image_format": image_format,
            "brightness_mean": brightness,
            "contrast_standard_deviation": contrast,
            "edge_variance": edge_variance,
            "quality_reasons": quality_reasons,
            "compression_analysis": compression,
            # M7 intentionally does not infer region-level tampering from these basic metrics.
            "anomaly_regions": [],
        })

    def _compression_metadata(self, image: Any, image_format: str) -> Dict[str, Any]:
        if image_format.upper() != "JPEG":
            return {
                "ela_available": False,
                "reason": "ela_heuristic_not_applicable_to_non_jpeg",
            }
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        with Image.open(BytesIO(buffer.getvalue())) as recompressed:
            difference = ImageChops.difference(image, recompressed.convert("RGB"))
            mean_difference = round(sum(ImageStat.Stat(difference).mean) / 3, 4)
        return {
            "ela_available": True,
            "ela_mean_difference": mean_difference,
            "heuristic": "JPEG recompression difference metric",
            "limitation": "Compression differences can result from scanning, resizing, recompression, normal editing, or export pipelines and are not proof of tampering.",
        }

    def _result(
        self,
        state: EvidenceState,
        confidence: float,
        details: Dict[str, Any],
        *,
        real_analysis_used: bool = True,
        fallback_used: bool = False,
        unavailable_mode: bool = False,
    ) -> VisualForensicsResult:
        return VisualForensicsResult(
            metadata={
                "source": "VISUAL_FORENSICS",
                "engine": self.engine_name,
                "real_analysis_used": real_analysis_used,
                "fallback_used": fallback_used,
                "unavailable_mode": unavailable_mode,
                **details,
            },
            evidence_state=state,
            confidence=confidence,
        )


def extract_visual_forensics_evidence(
    sample: CanonicalDocumentSample,
    adapter: VisualForensicsAdapter | None = None,
) -> List[EvidenceSignal]:
    """Map genuine computed image properties to zero-risk supporting evidence."""
    result = (adapter or PillowVisualForensicsAdapter()).analyze(sample.document_image)
    details = result.metadata
    if result.evidence_state == EvidenceState.POSITIVE:
        title = "Visual Image-Quality Analysis Completed"
        description = "Basic image-quality and available compression metrics were computed. This is supporting analysis only and does not authenticate the document."
        severity = SignalSeverity.INFO
    elif result.evidence_state == EvidenceState.MISSING:
        title = "Visual Analysis Input Missing"
        description = "No document image was available for visual analysis. Missing input is not a fraud signal."
        severity = SignalSeverity.INFO
    elif result.evidence_state == EvidenceState.UNRELIABLE:
        title = "Visual Analysis Reliability Limited"
        description = "Image quality metrics indicate the input may be insufficient for reliable visual analysis. This does not indicate tampering."
        severity = SignalSeverity.HIGH
    else:
        title = "Visual Analysis Unavailable"
        description = "The image could not be decoded for visual analysis. This is an availability limitation, not a fraud signal."
        severity = SignalSeverity.INFO

    return [EvidenceSignal(
        signal_id=f"SIG_VISUAL_RUNTIME_{sample.sample_id}",
        source="VISUAL_FORENSICS",
        category=SignalCategory.VISUAL_FORENSIC,
        evidence_state=result.evidence_state,
        severity=severity,
        title=title,
        description=description,
        confidence=result.confidence,
        contribution=0.0,
        limitation=result.limitation,
        raw_details=details,
    )]
