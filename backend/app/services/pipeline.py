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

from app.data.models import (
    CanonicalDocumentSample,
    MultimodalScreeningResult,
)
from app.services.synthetic_extractor import extract_synthetic_evidence
from app.services.ocr_adapter import extract_ocr_evidence
from app.services.mrz_adapter import extract_mrz_evidence
from app.services.visual_forensics_adapter import extract_visual_forensics_evidence
from app.services.biometric_adapter import extract_biometric_evidence
from app.services.risk_engine import (
    compute_uncertainty_score,
    compute_risk_score,
    determine_risk_level,
    get_recommendation,
)
from app.services.explanation_engine import generate_explanation


def run_screening_pipeline(
    sample: CanonicalDocumentSample,
    *,
    enable_ocr: bool = False,
    enable_mrz: bool = False,
    enable_visual_forensics: bool = False,
    enable_biometric_verification: bool = False,
) -> MultimodalScreeningResult:
    """
    Runs the full screening pipeline for a canonical document sample.
    Returns a MultimodalScreeningResult with evidence, conflicts, risk, and explanation.
    """
    screening_id = f"SCR-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"

    # Step 1: Extract modular evidence signals
    signals, conflicts, biometric_result = extract_synthetic_evidence(sample)

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

    # Step 2: Evaluate uncertainty from quality + signal reliability
    uncertainty_score = compute_uncertainty_score(
        sample.quality_metadata,
        signals,
        conflicts,
    )

    # Step 3: Evaluate risk from NEGATIVE signals and ACTUAL_CONTRADICTION conflicts
    risk_score = compute_risk_score(signals, conflicts)

    # Step 4: Determine four-state outcome (GREY takes precedence)
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
        pipeline_version="synthetic-deterministic-v1",
    )
