"""
Deterministic Synthetic Evidence Extractor (Milestone 4).

Produces structured EvidenceSignal and ConflictItem objects for each synthetic
demo case without invoking any AI/ML models. This establishes the end-to-end
pipeline contract and schema validation before advanced extractors are integrated.

IMPORTANT: All signals here are derived from known synthetic ground-truth metadata.
They are NOT predictions — they are deterministic representations of pre-defined
synthetic tampering scenarios, used to validate the pipeline architecture.

When real OCR, forensics, and biometric modules are integrated (Milestones 5–9),
they will produce signals through the same EvidenceSignal / ConflictItem schemas.
"""

from typing import List, Tuple
from app.data.models import (
    CanonicalDocumentSample,
    EvidenceSignal,
    ConflictItem,
    EvidenceState,
    SignalCategory,
    SignalSeverity,
    ConflictType,
    BiometricMatchResult,
    QualityMetadata,
)


def extract_synthetic_evidence(
    sample: CanonicalDocumentSample
) -> Tuple[List[EvidenceSignal], List[ConflictItem], BiometricMatchResult]:
    """
    Orchestrates deterministic evidence extraction based on sample_id.
    Returns: (evidence_signals, conflicts, biometric_result)
    """
    sid = sample.sample_id

    if sid == "CASE_001_GENUINE":
        return _extract_genuine_case()
    elif sid == "CASE_002_TAMPERED":
        return _extract_tampered_case()
    elif sid == "CASE_003_UNCERTAIN":
        return _extract_uncertain_case()
    else:
        # Fallback: return unavailable signals for unknown sample IDs
        return _extract_unknown_case(sid)


# ---------------------------------------------------------------------------
# Case 1: Genuine
# ---------------------------------------------------------------------------

def _extract_genuine_case() -> Tuple[List[EvidenceSignal], List[ConflictItem], BiometricMatchResult]:
    signals = [
        EvidenceSignal(
            signal_id="SIG_OCR_001",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="OCR Field Extraction Successful",
            description="All primary document fields extracted with high confidence: name, DOB, document number, nationality, and expiry date.",
            confidence=0.97,
            contribution=0.05,
            limitation="OCR accuracy is dependent on scan resolution and document condition.",
            raw_details={"fields_extracted": 8, "fields_failed": 0}
        ),
        EvidenceSignal(
            signal_id="SIG_MRZ_001",
            category=SignalCategory.STRUCTURAL_VALIDATION,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="MRZ Checksum Valid",
            description="All ICAO Doc 9303 checksums for document number, DOB, expiry, and composite field validated successfully.",
            confidence=1.0,
            contribution=0.05,
            limitation="Validates mathematical consistency only; does not verify document origin or issuing authority.",
            raw_details={"checksums_validated": 5, "checksums_failed": 0}
        ),
        EvidenceSignal(
            signal_id="SIG_DATE_001",
            category=SignalCategory.STRUCTURAL_VALIDATION,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="Date Consistency Check Passed",
            description="DOB, issue date, and expiry date are logically consistent. Document is not expired.",
            confidence=0.99,
            contribution=0.05,
            limitation="Dates cross-validated from OCR text only; no government registry confirmation.",
            raw_details={"dob": "1988-05-14", "expiry_date": "2031-05-13", "is_expired": False}
        ),
        EvidenceSignal(
            signal_id="SIG_VIS_001",
            category=SignalCategory.VISUAL_FORENSIC,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="No Strong Visual Manipulation Signal",
            description="ELA noise distribution is uniform across document regions. No abnormal compression artifacts detected around portrait or data fields.",
            confidence=0.82,
            contribution=0.05,
            limitation="Visual forensics can detect common digital manipulations but may not catch high-quality forgeries. Results are probabilistic indicators, not proof.",
            raw_details={"ela_anomaly_score": 0.08, "regions_analyzed": 4}
        ),
        EvidenceSignal(
            signal_id="SIG_BIO_001",
            category=SignalCategory.BIOMETRIC_VERIFICATION,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="Biometric Similarity: Match Signal",
            description="Face similarity distance between document portrait and live photo is within acceptance threshold.",
            confidence=0.88,
            contribution=0.05,
            limitation="[SYNTHETIC DEMO] Biometric result derived from ground-truth metadata. Real pretrained model integration planned for Milestone 8. Face similarity does not prove document authenticity.",
            raw_details={"similarity_distance": 0.14, "threshold": 0.40, "result": "MATCH"}
        ),
        EvidenceSignal(
            signal_id="SIG_CROSS_001",
            category=SignalCategory.CROSS_DOCUMENT_CONSISTENCY,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="Passport–Visa Cross-Document Consistency",
            description="Name, nationality, and document number relationship between passport and visa are consistent.",
            confidence=0.95,
            contribution=0.05,
            limitation="Cross-validation is limited to extracted text fields. Does not verify visa authenticity.",
            raw_details={"fields_matched": ["full_name", "nationality"], "fields_conflicted": []}
        ),
    ]
    conflicts: List[ConflictItem] = []
    biometric = BiometricMatchResult.MATCH
    return signals, conflicts, biometric


# ---------------------------------------------------------------------------
# Case 2: Tampered (Synthetic Scenario)
# ---------------------------------------------------------------------------

def _extract_tampered_case() -> Tuple[List[EvidenceSignal], List[ConflictItem], BiometricMatchResult]:
    signals = [
        EvidenceSignal(
            signal_id="SIG_OCR_002",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.POSITIVE,
            severity=SignalSeverity.INFO,
            title="OCR Field Extraction Successful",
            description="Primary document fields extracted. Visual DOB reads 1995-12-01.",
            confidence=0.95,
            contribution=0.05,
            limitation="OCR reflects visual surface content only. Does not detect digital alterations.",
            raw_details={"fields_extracted": 8, "fields_failed": 0, "visual_dob": "1995-12-01"}
        ),
        EvidenceSignal(
            signal_id="SIG_MRZ_002",
            category=SignalCategory.STRUCTURAL_VALIDATION,
            evidence_state=EvidenceState.NEGATIVE,
            severity=SignalSeverity.CRITICAL,
            title="MRZ DOB Checksum Mismatch",
            description="MRZ-encoded date of birth is 1990-12-01. Visual field displays 1995-12-01. Checksum validates 1990-12-01 only, indicating visual field has been altered.",
            confidence=0.98,
            contribution=0.35,
            limitation="MRZ checksum validates mathematical consistency per ICAO Doc 9303 only. Cannot determine method or intent of alteration.",
            raw_details={"visual_dob": "1995-12-01", "mrz_dob": "1990-12-01", "checksum_match": False}
        ),
        EvidenceSignal(
            signal_id="SIG_VIS_002",
            category=SignalCategory.VISUAL_FORENSIC,
            evidence_state=EvidenceState.NEGATIVE,
            severity=SignalSeverity.HIGH,
            title="Elevated ELA Noise at DOB Field and Portrait Boundary",
            description="Error Level Analysis indicates localized recompression artifacts around the date of birth text zone and portrait boundary, inconsistent with the surrounding document surface.",
            confidence=0.78,
            contribution=0.25,
            limitation="[SYNTHETIC DEMO] Visual forensics signal derived from ground-truth metadata. Real ELA module planned for Milestone 7. ELA can produce false positives on heavily scanned documents.",
            raw_details={"ela_anomaly_score": 0.74, "anomaly_regions": ["dob_text_zone", "portrait_boundary"]}
        ),
        EvidenceSignal(
            signal_id="SIG_BIO_002",
            category=SignalCategory.BIOMETRIC_VERIFICATION,
            evidence_state=EvidenceState.NEGATIVE,
            severity=SignalSeverity.HIGH,
            title="Biometric Disparity Signal: Possible Photo Replacement",
            description="Face similarity distance between document portrait and live photo exceeds acceptance threshold, indicating possible portrait substitution.",
            confidence=0.85,
            contribution=0.25,
            limitation="[SYNTHETIC DEMO] Biometric result derived from ground-truth metadata. Real pretrained model integration planned for Milestone 8. Mismatch does not constitute proof of identity fraud.",
            raw_details={"similarity_distance": 0.78, "threshold": 0.40, "result": "MISMATCH"}
        ),
        EvidenceSignal(
            signal_id="SIG_CROSS_002",
            category=SignalCategory.CROSS_DOCUMENT_CONSISTENCY,
            evidence_state=EvidenceState.NEGATIVE,
            severity=SignalSeverity.MEDIUM,
            title="DOB Conflict Detected Between Passport and Visa",
            description="Passport visual DOB (1995-12-01) does not match the DOB recorded on the secondary visa document (1990-12-01).",
            confidence=0.92,
            contribution=0.10,
            limitation="Cross-validation relies on OCR accuracy of both documents.",
            raw_details={"passport_dob": "1995-12-01", "visa_dob": "1990-12-01"}
        ),
    ]

    conflicts = [
        ConflictItem(
            conflict_id="CONF_DOB_001",
            source_a="VISUAL_OCR",
            source_b="MRZ_STRUCTURAL_VALIDATOR",
            field_name="date_of_birth",
            value_a="1995-12-01",
            value_b="1990-12-01",
            conflict_type=ConflictType.ACTUAL_CONTRADICTION,
            severity=SignalSeverity.CRITICAL,
            confidence=0.98,
            impact=0.40,
            resolvable=True,
            resolution_status="UNRESOLVED",
            explanation="Visual DOB field displays 1995-12-01 while MRZ checksum validates 1990-12-01. This is a structural contradiction between the document's visual layer and encoded data zone."
        ),
        ConflictItem(
            conflict_id="CONF_FACE_001",
            source_a="DOCUMENT_PORTRAIT",
            source_b="LIVE_PERSON_PHOTO",
            field_name="facial_identity",
            value_a="portrait_embedding",
            value_b="live_photo_embedding",
            conflict_type=ConflictType.ACTUAL_CONTRADICTION,
            severity=SignalSeverity.HIGH,
            confidence=0.85,
            impact=0.30,
            resolvable=True,
            resolution_status="UNRESOLVED",
            explanation="[SYNTHETIC DEMO] Face similarity distance (0.78) exceeds acceptance threshold (0.40), suggesting the document portrait and live photo do not correspond to the same individual."
        ),
    ]

    biometric = BiometricMatchResult.MISMATCH
    return signals, conflicts, biometric


# ---------------------------------------------------------------------------
# Case 3: Uncertain (Poor Quality)
# ---------------------------------------------------------------------------

def _extract_uncertain_case() -> Tuple[List[EvidenceSignal], List[ConflictItem], BiometricMatchResult]:
    signals = [
        EvidenceSignal(
            signal_id="SIG_QUAL_003",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.UNRELIABLE,
            severity=SignalSeverity.HIGH,
            title="Insufficient Document Image Quality",
            description="Severe motion blur (score: 0.78) and specular glare detected. Optical clarity is below the minimum threshold required for reliable field extraction.",
            confidence=0.95,
            contribution=0.0,
            limitation="Quality assessment measures optical properties only; does not imply document manipulation.",
            raw_details={"blur_score": 0.78, "glare_detected": True, "resolution": "640x480", "sufficient": False}
        ),
        EvidenceSignal(
            signal_id="SIG_OCR_003",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.UNRELIABLE,
            severity=SignalSeverity.HIGH,
            title="OCR Extraction Unreliable",
            description="OCR confidence is 0.25 due to motion blur and glare. Only partial text was recoverable. Extracted fields cannot be relied upon for forensic comparison.",
            confidence=0.25,
            contribution=0.0,
            limitation="Low extraction confidence. Results should not be used as basis for fraud determination.",
            raw_details={"fields_extracted": 3, "fields_failed": 5, "ocr_confidence": 0.25}
        ),
        EvidenceSignal(
            signal_id="SIG_MRZ_003",
            category=SignalCategory.STRUCTURAL_VALIDATION,
            evidence_state=EvidenceState.UNRELIABLE,
            severity=SignalSeverity.HIGH,
            title="MRZ Zone Unreadable",
            description="MRZ zone is obscured by glare and blur. Checksum validation cannot be performed. This is not evidence of tampering; it reflects insufficient image quality.",
            confidence=0.90,
            contribution=0.0,
            limitation="Inability to validate MRZ does not imply fraud. Manual re-capture required.",
            raw_details={"mrz_readable": False, "reason": "motion_blur_and_glare"}
        ),
        EvidenceSignal(
            signal_id="SIG_VIS_003",
            category=SignalCategory.VISUAL_FORENSIC,
            evidence_state=EvidenceState.UNRELIABLE,
            severity=SignalSeverity.MEDIUM,
            title="Visual Forensics Inconclusive",
            description="ELA analysis cannot differentiate between compression artifacts caused by manipulation and those caused by motion blur and recompression from poor capture conditions.",
            confidence=0.30,
            contribution=0.0,
            limitation="Visual forensics requires a minimum quality standard. Results on degraded images are not reliable.",
            raw_details={"ela_anomaly_score": 0.55, "quality_disqualified": True}
        ),
        EvidenceSignal(
            signal_id="SIG_BIO_003",
            category=SignalCategory.BIOMETRIC_VERIFICATION,
            evidence_state=EvidenceState.UNRELIABLE,
            severity=SignalSeverity.MEDIUM,
            title="Biometric Comparison Inconclusive",
            description="Document portrait cannot be extracted reliably from the blurred scan. Face comparison result is inconclusive and does not contribute to risk assessment.",
            confidence=0.20,
            contribution=0.0,
            limitation="[SYNTHETIC DEMO] Biometric result derived from quality assessment. Inconclusive result does not indicate fraud.",
            raw_details={"result": "INCONCLUSIVE", "reason": "portrait_unreadable"}
        ),
    ]

    # No explicit conflicts — unreadable data is NOT contradictory data
    conflicts: List[ConflictItem] = []
    biometric = BiometricMatchResult.INCONCLUSIVE
    return signals, conflicts, biometric


# ---------------------------------------------------------------------------
# Fallback for unknown sample IDs
# ---------------------------------------------------------------------------

def _extract_unknown_case(sample_id: str) -> Tuple[List[EvidenceSignal], List[ConflictItem], BiometricMatchResult]:
    signals = [
        EvidenceSignal(
            signal_id="SIG_UNKNOWN_001",
            category=SignalCategory.DOCUMENT_INTELLIGENCE,
            evidence_state=EvidenceState.UNAVAILABLE,
            severity=SignalSeverity.INFO,
            title="No Deterministic Evidence Available",
            description=f"Sample ID '{sample_id}' is not in the synthetic dataset registry. Evidence extraction is unavailable.",
            confidence=0.0,
            contribution=0.0,
            limitation="Only CASE_001_GENUINE, CASE_002_TAMPERED, and CASE_003_UNCERTAIN are supported in the synthetic pipeline."
        ),
    ]
    return signals, [], BiometricMatchResult.UNAVAILABLE
