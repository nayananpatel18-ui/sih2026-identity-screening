"""
Canonical Data Models for SIH 2026 AI Identity Screening System.
Provides dataset-agnostic representations for documents, evidence signals, and risk outputs.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentType(str, Enum):
    PASSPORT = "PASSPORT"
    VISA = "VISA"
    NATIONAL_ID = "NATIONAL_ID"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    GREEN = "GREEN"    # Low risk / consistent evidence
    AMBER = "AMBER"    # Suspicious signals / further attention recommended
    RED = "RED"        # Multiple strong suspicious signals / human review required
    GREY = "GREY"      # Insufficient or unreliable evidence / cannot assess


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


class QualityMetadata(BaseModel):
    blur_score: float = 0.0
    glare_detected: bool = False
    is_partial: bool = False
    resolution_w: int = 0
    resolution_h: int = 0
    is_sufficient_quality: bool = True
    notes: Optional[str] = None


class TamperMetadata(BaseModel):
    is_tampered: bool = False
    tamper_types: List[str] = Field(default_factory=list)  # e.g., ["dob_change", "photo_replace"]
    tamper_regions: List[Dict[str, Any]] = Field(default_factory=list)
    description: Optional[str] = None


class CanonicalExtractedFields(BaseModel):
    given_names: Optional[str] = None
    surname: Optional[str] = None
    full_name: Optional[str] = None
    dob: Optional[str] = None                # Format: YYYY-MM-DD
    gender: Optional[str] = None
    nationality: Optional[str] = None
    document_number: Optional[str] = None
    expiry_date: Optional[str] = None        # Format: YYYY-MM-DD
    issue_date: Optional[str] = None         # Format: YYYY-MM-DD
    issuing_country: Optional[str] = None
    mrz_raw: Optional[str] = None
    raw_ocr_text: Optional[str] = None


class GroundTruthMetadata(BaseModel):
    is_tampered: bool = False
    tamper_details: Optional[TamperMetadata] = None
    expected_risk: RiskLevel = RiskLevel.GREEN
    expected_fields: Optional[CanonicalExtractedFields] = None


class CanonicalDocumentSample(BaseModel):
    """
    Standardized internal representation of a document screening sample.
    Consumed directly by the screening pipeline regardless of source dataset.
    """
    sample_id: str
    source_dataset: str                       # e.g. "synthetic", "midv500", "midv2020", "doctamper", "idnet"
    document_type: DocumentType = DocumentType.PASSPORT
    
    # Image references / paths
    document_image: str                        # Path or URI to primary document
    secondary_document_image: Optional[str] = None  # e.g. Visa image
    person_image: Optional[str] = None         # Live photo of individual
    
    # Extracted or Ground Truth info
    extracted_fields: Optional[CanonicalExtractedFields] = None
    quality_metadata: QualityMetadata = Field(default_factory=QualityMetadata)
    ground_truth: Optional[GroundTruthMetadata] = None
    
    # Audit tracking
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceSignal(BaseModel):
    """Structured evidence item produced by forensic / validation modules."""
    signal_id: str
    category: SignalCategory
    severity: SignalSeverity
    title: str
    description: str
    confidence: float = 1.0                    # 0.0 to 1.0
    evidence_data: Dict[str, Any] = Field(default_factory=dict)


class ScreeningResult(BaseModel):
    """Full multimodal screening output."""
    screening_id: str
    sample_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "COMPLETED"
    
    risk_level: RiskLevel
    risk_score: float                          # 0.0 (safest) to 1.0 (highest risk)
    uncertainty_score: float                   # 0.0 (high certainty) to 1.0 (low certainty / poor evidence)
    
    extracted_fields: Optional[CanonicalExtractedFields] = None
    quality_metadata: QualityMetadata = Field(default_factory=QualityMetadata)
    
    evidence_signals: List[EvidenceSignal] = Field(default_factory=list)
    explanation: str = ""
    recommendation: str = ""                   # CLEAR, FURTHER_VERIFICATION, HUMAN_REVIEW
