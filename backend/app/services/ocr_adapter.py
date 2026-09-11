"""Small, replaceable OCR adapter boundary for M5.1.

The current environment has no installed local OCR engine.  The fallback below
only recognizes the project's explicitly labelled synthetic PNG fixtures and
returns a transcription of text visibly printed on them.  It is intentionally
not used by the M4 deterministic screening pipeline.
"""

from dataclasses import dataclass, field
import importlib.util
from pathlib import Path
import re
import shutil
from typing import Dict, List, Protocol

from PIL import Image, UnidentifiedImageError

from app.data.models import (
    CanonicalDocumentSample,
    CanonicalExtractedFields,
    EvidenceSignal,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
)


@dataclass
class OcrExtractionResult:
    """Engine-neutral OCR output for future OCR providers."""

    raw_text: str = ""
    fields: CanonicalExtractedFields = field(default_factory=CanonicalExtractedFields)
    metadata: Dict[str, object] = field(default_factory=dict)
    evidence_state: EvidenceState = EvidenceState.UNAVAILABLE


@dataclass(frozen=True)
class OcrCapability:
    """Availability of the optional local Tesseract boundary."""

    real_engine_available: bool
    engine: str
    reason: str


class OcrAdapter(Protocol):
    """Contract implemented by local OCR engines or controlled demo fallbacks."""

    def extract(self, image_path: str | Path) -> OcrExtractionResult:
        """Read an image and return extracted text, normalized fields, and metadata."""


def detect_ocr_capability() -> OcrCapability:
    """Detect, without installing or invoking, the supported local OCR engine."""
    tesseract_path = shutil.which("tesseract")
    has_pytesseract = importlib.util.find_spec("pytesseract") is not None
    if tesseract_path and has_pytesseract:
        return OcrCapability(True, "tesseract", "Local Tesseract executable and pytesseract binding detected.")
    if not tesseract_path and not has_pytesseract:
        reason = "Tesseract executable and pytesseract binding are not installed."
    elif not tesseract_path:
        reason = "Tesseract executable is not installed or not on PATH."
    else:
        reason = "pytesseract binding is not installed."
    return OcrCapability(False, "tesseract", reason)


_SYNTHETIC_FIXTURE_TRANSCRIPTIONS = {
    "passport_001.png": (
        "SYNTHETIC DEMO DOCUMENT\nNOT A REAL IDENTITY DOCUMENT\nDEMO PASSPORT\n"
        "NAME: RAJESH KUMAR SHARMA\nDOCUMENT NO: DEMO-Z1234567\n"
        "NATIONALITY: DEMO\nDOB: 1990-01-01\nSTATUS: CONSISTENT DEMO INPUT",
        {
            "full_name": "RAJESH KUMAR SHARMA",
            "document_number": "DEMO-Z1234567",
            "nationality": "DEMO",
            "dob": "1990-01-01",
        },
    ),
    "passport_002_dob_mod.png": (
        "SYNTHETIC DEMO DOCUMENT\nNOT A REAL IDENTITY DOCUMENT\nDEMO PASSPORT\n"
        "NAME: ANITA ROY\nDOCUMENT NO: DEMO-K9876543\n"
        "STATUS: SYNTHETIC TAMPER SCENARIO",
        {
            "full_name": "ANITA ROY",
            "document_number": "DEMO-K9876543",
        },
    ),
    "passport_003_blurred.png": (
        "SYNTHETIC DEMO DOCUMENT\nNOT A REAL IDENTITY DOCUMENT\nDEMO PASSPORT\n"
        "NAME: VIKRAM S DEMO\nDOCUMENT NO: DEMO-J55XX89\n"
        "NATIONALITY: DEMO\nDOB: 1990-01-01\nSTATUS: LOW-CLARITY DEMO INPUT",
        {
            "full_name": "VIKRAM S DEMO",
            "document_number": "DEMO-J55XX89",
            "nationality": "DEMO",
            "dob": "1990-01-01",
        },
    ),
}


class SyntheticFixtureOcrAdapter:
    """Deterministic, fixture-only fallback used until a local OCR engine is available."""

    engine_name = "synthetic_fixture_fallback"

    def __init__(self, capability: OcrCapability | None = None):
        self.capability = capability or detect_ocr_capability()

    def extract(self, image_path: str | Path) -> OcrExtractionResult:
        path = Path(image_path)
        if not path.is_file():
            path = Path(__file__).resolve().parents[3] / path
        if not path.is_file():
            return self._unavailable("Image path does not exist.")

        try:
            with Image.open(path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError):
            return self._unavailable("Image could not be read safely.")

        transcription = _SYNTHETIC_FIXTURE_TRANSCRIPTIONS.get(path.name)
        if not transcription:
            return self._unavailable("No deterministic fallback transcription exists for this image.")

        raw_text, fields = transcription
        low_clarity_fixture = path.name == "passport_003_blurred.png"
        return OcrExtractionResult(
            raw_text=raw_text,
            fields=CanonicalExtractedFields(**fields),
            metadata={
                "source": "OCR",
                "engine": self.engine_name,
                "fallback_used": True,
                "fixture_only": True,
                "demo_only": True,
                "adapter_path": "synthetic_fixture_fallback",
                "real_engine_available": self.capability.real_engine_available,
                "real_engine_status": "available_not_used" if self.capability.real_engine_available else "unavailable",
                "real_engine_reason": self.capability.reason,
                "quality_limitation": "low_clarity_fixture" if low_clarity_fixture else None,
            },
            evidence_state=EvidenceState.UNRELIABLE if low_clarity_fixture else EvidenceState.POSITIVE,
        )

    def _unavailable(self, reason: str) -> OcrExtractionResult:
        return OcrExtractionResult(
            metadata={
                "source": "OCR",
                "engine": self.engine_name,
                "fallback_used": True,
                "demo_only": True,
                "adapter_path": "synthetic_fixture_fallback",
                "real_engine_available": self.capability.real_engine_available,
                "real_engine_status": "available_not_used" if self.capability.real_engine_available else "unavailable",
                "real_engine_reason": self.capability.reason,
                "reason": reason,
            },
            evidence_state=EvidenceState.UNAVAILABLE,
        )


class TesseractOcrAdapter:
    """Optional local real-engine adapter, used only when its capability is available."""

    engine_name = "tesseract"

    def extract(self, image_path: str | Path) -> OcrExtractionResult:
        path = Path(image_path)
        if not path.is_file():
            path = Path(__file__).resolve().parents[3] / path
        if not path.is_file():
            return self._unavailable("Image path does not exist.")

        try:
            import pytesseract
            raw_text = pytesseract.image_to_string(str(path)).strip()
        except Exception as error:
            return self._unavailable(f"Local Tesseract extraction failed: {error}")

        if not raw_text:
            return self._unavailable("Local Tesseract returned no text.")
        return OcrExtractionResult(
            raw_text=raw_text,
            fields=_normalize_labeled_fields(raw_text),
            metadata={
                "source": "OCR",
                "engine": self.engine_name,
                "fallback_used": False,
                "demo_only": False,
                "adapter_path": "local_real_engine",
                "real_engine_available": True,
                "real_engine_status": "used",
            },
            evidence_state=EvidenceState.POSITIVE,
        )

    def _unavailable(self, reason: str) -> OcrExtractionResult:
        return OcrExtractionResult(
            metadata={
                "source": "OCR",
                "engine": self.engine_name,
                "fallback_used": False,
                "adapter_path": "local_real_engine",
                "real_engine_available": True,
                "real_engine_status": "failed",
                "reason": reason,
            },
            evidence_state=EvidenceState.UNAVAILABLE,
        )


def get_ocr_adapter(capability: OcrCapability | None = None) -> OcrAdapter:
    """Select real local OCR only when it is fully available; otherwise use the demo fallback."""
    capability = capability or detect_ocr_capability()
    if capability.real_engine_available:
        return TesseractOcrAdapter()
    return SyntheticFixtureOcrAdapter(capability)


def _normalize_labeled_fields(raw_text: str) -> CanonicalExtractedFields:
    """Minimal label parser for the optional local engine; absent labels remain absent."""
    labels = {
        "full_name": r"(?:NAME|FULL NAME)\s*:\s*([^\n]+)",
        "document_number": r"(?:DOCUMENT NO|DOCUMENT NUMBER)\s*:\s*([^\n]+)",
        "nationality": r"NATIONALITY\s*:\s*([^\n]+)",
        "dob": r"(?:DOB|DATE OF BIRTH)\s*:\s*([^\n]+)",
        "expiry_date": r"(?:EXPIRY DATE|DATE OF EXPIRY)\s*:\s*([^\n]+)",
        "issue_date": r"(?:ISSUE DATE|DATE OF ISSUE)\s*:\s*([^\n]+)",
        "gender": r"(?:SEX|GENDER)\s*:\s*([^\n]+)",
    }
    values = {}
    for field_name, pattern in labels.items():
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if match:
            values[field_name] = match.group(1).strip()
    return CanonicalExtractedFields(**values)


_OCR_FIELD_NAMES = (
    "full_name",
    "document_number",
    "dob",
    "nationality",
    "expiry_date",
    "issue_date",
    "gender",
)


def extract_ocr_evidence(
    sample: CanonicalDocumentSample,
    adapter: OcrAdapter | None = None,
) -> List[EvidenceSignal]:
    """Convert optional OCR output into zero-risk, officer-reviewable evidence."""
    result = (adapter or get_ocr_adapter()).extract(sample.document_image)
    extracted_fields = result.fields.model_dump(exclude_none=True)
    missing_fields = [name for name in _OCR_FIELD_NAMES if getattr(result.fields, name) is None]
    raw_details = {
        "ocr_metadata": result.metadata,
        "extracted_fields": extracted_fields,
        "missing_fields": missing_fields,
        "raw_text": result.raw_text,
    }

    if result.evidence_state == EvidenceState.UNAVAILABLE:
        return [EvidenceSignal(
            signal_id=f"SIG_OCR_RUNTIME_{sample.sample_id}",
            source="OCR",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.UNAVAILABLE,
            severity=SignalSeverity.INFO,
            title="OCR Extraction Unavailable",
            description="OCR could not produce text for this input. This is an availability limitation, not a fraud signal.",
            confidence=0.0,
            contribution=0.0,
            limitation="The configured OCR adapter is a deterministic synthetic-fixture fallback, not a production OCR engine.",
            raw_details=raw_details,
        )]

    extraction_signal = EvidenceSignal(
        signal_id=f"SIG_OCR_RUNTIME_{sample.sample_id}",
        source="OCR",
        category=SignalCategory.DOCUMENT_INTELLIGENCE,
        evidence_state=result.evidence_state,
        severity=SignalSeverity.HIGH if result.evidence_state == EvidenceState.UNRELIABLE else SignalSeverity.INFO,
        title="Synthetic OCR Fallback Extraction" if result.evidence_state == EvidenceState.POSITIVE else "Synthetic OCR Fallback Extraction Unreliable",
        description=(
            "Text was transcribed by the deterministic synthetic-fixture fallback. It is demo-only OCR evidence and does not verify document authenticity."
            if result.evidence_state == EvidenceState.POSITIVE
            else "Text was transcribed by the deterministic synthetic-fixture fallback, but the fixture is marked low clarity. The extracted text must not be relied upon for comparison."
        ),
        confidence=0.60 if result.evidence_state == EvidenceState.POSITIVE else 0.25,
        contribution=0.0,
        limitation="Synthetic deterministic fallback only; replace with a local OCR engine before using non-fixture inputs.",
        raw_details=raw_details,
    )
    signals = [extraction_signal]

    if missing_fields:
        signals.append(EvidenceSignal(
            signal_id=f"SIG_OCR_MISSING_{sample.sample_id}",
            source="OCR",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.MISSING,
            severity=SignalSeverity.INFO,
            title="OCR Fields Not Present",
            description="Some supported fields were not present in the OCR output. Missing fields are not fraud indicators.",
            confidence=1.0,
            contribution=0.0,
            limitation="The fallback reports only visibly transcribed fixture fields.",
            raw_details={"missing_fields": missing_fields},
        ))

    return signals
