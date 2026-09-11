"""
Screening Pipeline Orchestrator.

Orchestrates modular, sequential evidence extractors through a common pipeline
for a given CanonicalDocumentSample.

Architecture Note:
  Extractors are currently invoked sequentially (deterministic prototype).
  Actual concurrency is not required and would complicate debugging in this phase.
  When real ML models are integrated (Milestones 5-9), each module replaces its
  corresponding synthetic signal set without altering pipeline contracts.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from app.data.models import (
    CanonicalDocumentSample,
    ConflictItem,
    EvidenceSignal,
    MultimodalScreeningResult,
    OfficerReviewResult,
)
from app.services.synthetic_extractor import extract_synthetic_evidence
from app.services.ocr_adapter import extract_ocr_evidence
from app.services.mrz_adapter import extract_mrz_evidence
from app.services.visual_forensics_adapter import extract_visual_forensics_evidence
from app.services.biometric_adapter import extract_biometric_evidence
from app.services.cross_document_consistency import extract_cross_document_evidence
from app.services.evidence_fusion import MultimodalEvidenceFusionEngine, fusion_evidence_signal
from app.services.risk_engine import (
    compute_uncertainty_score,
    compute_risk_score,
    determine_risk_level,
    get_recommendation,
)
from app.services.explanation_engine import generate_explanation
from app.services.officer_review import OfficerReviewService


def run_screening_pipeline(
    sample: CanonicalDocumentSample,
    *,
    enable_ocr: bool = False,
    enable_mrz: bool = False,
    enable_visual_forensics: bool = False,
    enable_biometric_verification: bool = False,
    enable_cross_document_consistency: bool = False,
    enable_evidence_fusion: bool = False,
    enable_officer_review: bool = False,
    evaluation_signals: Optional[List[EvidenceSignal]] = None,
    evaluation_conflicts: Optional[List[ConflictItem]] = None,
) -> MultimodalScreeningResult:
    """
    Runs the full screening pipeline for a canonical document sample.
    Returns a MultimodalScreeningResult with evidence, conflicts, risk, and explanation.
    """
    screening_id = f"SCR-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"

    # Step 1: Extract modular evidence signals
    signals, conflicts, biometric_result = extract_synthetic_evidence(sample)

    # M12 passes controlled synthetic adapter observations through this internal
    # hook.  Normal API requests cannot supply these values, so M1-M11 behaviour
    # remains unchanged.  The existing risk, uncertainty, fusion and review
    # paths below remain the sole decision-support implementation.
    if evaluation_signals:
        signals.extend(evaluation_signals)
    if evaluation_conflicts:
        conflicts.extend(evaluation_conflicts)

    # OCR integration is opt-in so M4/M4.5's deterministic default remains intact.
    if enable_ocr:
        signals.extend(extract_ocr_evidence(sample))

    # MRZ validation is opt-in and does not alter M4/M5 defaults or risk weighting.
    if enable_mrz:
        signals.extend(extract_mrz_evidence(sample))

    # Basic visual analysis is opt-in and emits supporting, zero-risk evidence only.
    if enable_visual_forensics:
        signals.extend(extract_visual_forensics_evidence(sample))

    # M8 remains opt-in; its fallback produces zero-risk supporting evidence only.
    if enable_biometric_verification:
        signals.extend(extract_biometric_evidence(sample))

    # M9 compares only explicitly supplied structured fields and is opt-in.
    if enable_cross_document_consistency:
        cross_document_signals, cross_document_conflicts = extract_cross_document_evidence(sample)
        signals.extend(cross_document_signals)
        conflicts.extend(cross_document_conflicts)

    # Step 2: M10 optionally summarizes existing evidence using the established
    # risk/uncertainty functions. The summary has zero contribution of its own.
    if enable_evidence_fusion:
        fusion_result = MultimodalEvidenceFusionEngine().fuse(signals, conflicts, sample.quality_metadata)
        risk_score = fusion_result.risk_score
        uncertainty_score = fusion_result.uncertainty_score
        risk_level = fusion_result.risk_level
        signals.append(fusion_evidence_signal(fusion_result))
    else:
        uncertainty_score = compute_uncertainty_score(sample.quality_metadata, signals, conflicts)
        risk_score = compute_risk_score(signals, conflicts)
        risk_level = determine_risk_level(risk_score, uncertainty_score)

    # Step 5: Generate explanation text grounded in evidence signals
    explanation = generate_explanation(
        risk_level=risk_level,
        risk_score=risk_score,
        uncertainty_score=uncertainty_score,
        signals=signals,
        conflicts=conflicts,
        biometric_result=biometric_result,
    )

    # Step 6: Get cautious decision-support recommendation
    recommendation = get_recommendation(risk_level)

    officer_review: OfficerReviewResult | None = None
    if enable_officer_review:
        officer_review = OfficerReviewService().build(
            screening_id=screening_id,
            risk_level=risk_level,
            risk_score=risk_score,
            uncertainty_score=uncertainty_score,
            signals=signals,
            conflicts=conflicts,
            recommendation=recommendation,
        )

    return MultimodalScreeningResult(
        screening_id=screening_id,
        sample_id=sample.sample_id,
        risk_level=risk_level,
        risk_score=risk_score,
        uncertainty_score=uncertainty_score,
        extracted_fields=sample.extracted_fields,
        quality_metadata=sample.quality_metadata,
        evidence_signals=signals,
        conflicts=conflicts,
        biometric_result=biometric_result,
        explanation=explanation,
        recommendation=recommendation,
        officer_review=officer_review,
        pipeline_version="synthetic-deterministic-v1",
    )
