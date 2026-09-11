"""
Canonical Data Models for SIH 2026 AI Identity Screening System.
Provides dataset-agnostic representations for documents, evidence signals,
conflicts, biometric signals, and multimodal screening results.

Design Principles:
- confidence = reliability of the individual signal (0.0 to 1.0)
- contribution = influence weight on the risk score (0.0 to 1.0)
- These must NOT be treated as equivalent or as probabilities of fraud.
- Uncertainty takes precedence over risk when evidence is insufficient.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Risk & Decision Enums
# ---------------------------------------------------------------------------

class DocumentType(str, Enum):
    PASSPORT = "PASSPORT"
    VISA = "VISA"
    NATIONAL_ID = "NATIONAL_ID"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    GREEN = "GREEN"    # Low risk / consistent evidence -> Routine Clearance Recommended
    AMBER = "AMBER"    # Suspicious signals / minor conflicts -> Further Verification Recommended
    RED = "RED"        # Multiple strong suspicious signals / unresolved conflicts -> Secondary Inspection Recommended
    GREY = "GREY"      # High uncertainty / poor quality / missing critical evidence -> Manual Officer Review


class SignalCategory(str, Enum):
    DOCUMENT_INTELLIGENCE = "DOCUMENT_INTELLIGENCE"
    STRUCTURAL_VALIDATION = "STRUCTURAL_VALIDATION"
    VISUAL_FORENSIC = "VISUAL_FORENSIC"
    BIOMETRIC_VERIFICATION = "BIOMETRIC_VERIFICATION"
    CROSS_DOCUMENT_CONSISTENCY = "CROSS_DOCUMENT_CONSISTENCY"


class SignalSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceState(str, Enum):
    """
    Explicit state of an evidence signal.

    POSITIVE      - Signal validates consistency (e.g. MRZ checksum matches visual DOB)
    NEGATIVE      - Signal indicates anomaly or discrepancy (e.g. ELA noise mismatch)
    MISSING       - Input was not provided (e.g. no secondary visa uploaded)
    UNAVAILABLE   - Extractor could not run (e.g. OCR service unavailable)
    UNRELIABLE    - Low clarity / noise prevents confident analysis (blur, glare)
    NOT_APPLICABLE - Check is not valid for this document type (e.g. no MRZ on ID card)
    """
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    UNRELIABLE = "UNRELIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ConflictType(str, Enum):
    """
    Strict hierarchy: missing/unreadable data is NOT equivalent to contradictory data.

    ACTUAL_CONTRADICTION - Clear contradictory values across two sources (raises Risk)
    UNREADABLE_EVIDENCE  - Text/MRZ unreadable, not necessarily fraudulent (raises Uncertainty)
    UNRELIABLE_EVIDENCE  - Low confidence extraction, caution warranted (raises Uncertainty)
    MISSING_EVIDENCE     - Input not provided, no inference possible (no Risk/Uncertainty penalty)
    """
    ACTUAL_CONTRADICTION = "ACTUAL_CONTRADICTION"
    UNREADABLE_EVIDENCE = "UNREADABLE_EVIDENCE"
    UNRELIABLE_EVIDENCE = "UNRELIABLE_EVIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


class BiometricMatchResult(str, Enum):
    """
    Biometric verification outcomes.
    Handcrafted descriptors are NOT labeled as biometric embeddings.
    """
    MATCH = "MATCH"                # Similarity distance below threshold
    MISMATCH = "MISMATCH"          # Similarity distance above threshold
    INCONCLUSIVE = "INCONCLUSIVE"  # Low resolution / lighting prevents confident comparison
    UNAVAILABLE = "UNAVAILABLE"    # No person photo or document portrait present


# ---------------------------------------------------------------------------
# Quality Metadata
# ---------------------------------------------------------------------------

class QualityMetadata(BaseModel):
    blur_score: float = 0.0             # 0.0 = sharp, 1.0 = maximally blurred
    glare_detected: bool = False
    is_partial: bool = False
    resolution_w: int = 0
    resolution_h: int = 0
    is_sufficient_quality: bool = True
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Evidence Signals
# ---------------------------------------------------------------------------

class EvidenceSignal(BaseModel):
    """
    Structured evidence item produced by forensic / validation modules.

    Fields:
        confidence   - Reliability of this individual signal (0.0 = unreliable, 1.0 = highly reliable)
                       NOT the probability that fraud occurred.
        contribution - Influence weight this signal contributes to the Risk Score (0.0 to 1.0)
                       NOT the same as confidence. A low-confidence signal may have high contribution
                       weight (and vice versa), depending on module and severity context.
    """
    signal_id: str
    source: str = "SYNTHETIC_DEMO"
    category: SignalCategory
    evidence_state: EvidenceState
    severity: SignalSeverity
    title: str
    description: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    contribution: float = Field(default=0.0, ge=0.0, le=1.0)
    limitation: Optional[str] = None
    raw_details: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Conflict Model
# ---------------------------------------------------------------------------

class ConflictItem(BaseModel):
    """
    Explicitly represents a discrepancy discovered across evidence sources.
    Only ACTUAL_CONTRADICTION raises the Risk Score.
    UNREADABLE/UNRELIABLE types raise the Uncertainty Score.
    MISSING_EVIDENCE does not raise either score.
    """
    conflict_id: str
    source_a: str
    source_b: str
    field_name: str
    value_a: Optional[str] = None      # May be None for missing evidence
    value_b: Optional[str] = None
    conflict_type: ConflictType
    severity: SignalSeverity
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    impact: float = Field(default=0.0, ge=0.0, le=1.0)
    resolvable: bool = True
    resolution_status: str = "UNRESOLVED"   # UNRESOLVED, RESOLVED, DEFERRED
    explanation: str = ""


# ---------------------------------------------------------------------------
# Canonical Document Sample (Adapter Output)
# ---------------------------------------------------------------------------

class TamperMetadata(BaseModel):
    is_tampered: bool = False
    tamper_types: List[str] = Field(default_factory=list)
    tamper_regions: List[Dict[str, Any]] = Field(default_factory=list)
    description: Optional[str] = None


class GroundTruthMetadata(BaseModel):
    is_tampered: bool = False
    tamper_details: Optional[TamperMetadata] = None
    expected_risk: RiskLevel = RiskLevel.GREEN


class CanonicalExtractedFields(BaseModel):
    given_names: Optional[str] = None
    surname: Optional[str] = None
    full_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    document_number: Optional[str] = None
    expiry_date: Optional[str] = None
    issue_date: Optional[str] = None
    issuing_country: Optional[str] = None
    mrz_raw: Optional[str] = None
    raw_ocr_text: Optional[str] = None


class CanonicalDocumentSample(BaseModel):
    """
    Standardized internal representation of a document screening sample.
    Consumed directly by the screening pipeline regardless of source dataset.
    Missing fields are represented safely (None / defaults).
    """
    sample_id: str
    source_dataset: str
    document_type: DocumentType = DocumentType.PASSPORT
    document_image: str
    secondary_document_image: Optional[str] = None
    person_image: Optional[str] = None
    extracted_fields: Optional[CanonicalExtractedFields] = None
    quality_metadata: QualityMetadata = Field(default_factory=QualityMetadata)
    ground_truth: Optional[GroundTruthMetadata] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Officer-Facing Sample View
# ---------------------------------------------------------------------------

class OfficerFacingDocumentSample(BaseModel):
    """Safe sample-inspection view that deliberately omits evaluation ground truth."""
    sample_id: str
    source_dataset: str
    document_type: DocumentType = DocumentType.PASSPORT
    document_image: str
    secondary_document_image: Optional[str] = None
    person_image: Optional[str] = None
    extracted_fields: Optional[CanonicalExtractedFields] = None
    quality_metadata: QualityMetadata = Field(default_factory=QualityMetadata)
    created_at: str
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Officer Review Output
# ---------------------------------------------------------------------------

class OfficerReviewFinding(BaseModel):
    signal_id: str
    source: str
    category: SignalCategory
    title: str
    description: str
    severity: SignalSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)


class OfficerReviewConflict(BaseModel):
    conflict_id: str
    field_name: str
    source_a: str
    source_b: str
    value_a: Optional[str] = None
    value_b: Optional[str] = None
    severity: SignalSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    impact: float = Field(ge=0.0, le=1.0)
    resolution_status: str
    explanation: str


class OfficerReviewResult(BaseModel):
    screening_id: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    overall_assessment: str
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    key_positive_findings: List[OfficerReviewFinding] = Field(default_factory=list)
    key_suspicious_findings: List[OfficerReviewFinding] = Field(default_factory=list)
    conflicts: List[OfficerReviewConflict] = Field(default_factory=list)
    uncertainty_reasons: List[str] = Field(default_factory=list)
    recommended_verifications: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    recommendation: str
    human_decision_required: bool = True


# ---------------------------------------------------------------------------
# M15 AI Advisory Reasoning Output
# ---------------------------------------------------------------------------

class AIRiskReasoningResult(BaseModel):
    """Advisory-only reasoning grounded in the supplied deterministic evidence."""
    advisory: bool = True
    provider: str = "deterministic-local"
    reasoning_summary: str
    key_risk_factors: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    uncertainty_factors: List[str] = Field(default_factory=list)
    conflicting_evidence: List[str] = Field(default_factory=list)
    recommended_verifications: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: List[str] = Field(default_factory=list)
    human_decision_required: bool = True


# ---------------------------------------------------------------------------
# Multimodal Screening Output
# ---------------------------------------------------------------------------

class MultimodalScreeningResult(BaseModel):
    """
    Full multimodal screening output from the pipeline.

    Decision Semantics:
      GREEN  - Low Risk / Evidence Consistent    -> Routine Clearance Recommended
      AMBER  - Suspicious Signals / Minor Issues -> Further Verification Recommended
      RED    - Multiple Suspicious Signals / Unresolved High-Impact Conflicts
                                                 -> Secondary Inspection Recommended
      GREY   - High Uncertainty / Insufficient or Unreliable Evidence
                                                 -> Manual Officer Review Required

    GREY takes precedence whenever uncertainty_score >= 0.65,
    regardless of the computed risk_score.
    """
    screening_id: str
    sample_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "COMPLETED"

    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)

    extracted_fields: Optional[CanonicalExtractedFields] = None
    quality_metadata: QualityMetadata = Field(default_factory=QualityMetadata)

    evidence_signals: List[EvidenceSignal] = Field(default_factory=list)
    conflicts: List[ConflictItem] = Field(default_factory=list)
    biometric_result: BiometricMatchResult = BiometricMatchResult.UNAVAILABLE

    explanation: str = ""
    recommendation: str = ""
    officer_review: Optional[OfficerReviewResult] = None
    ai_risk_reasoning: Optional[AIRiskReasoningResult] = Field(default=None, exclude_if=lambda value: value is None)
    pipeline_version: str = "synthetic-deterministic-v1"
