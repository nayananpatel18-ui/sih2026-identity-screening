"""
Screenings API Route.
POST /api/screenings/run — Runs the full screening pipeline for a named synthetic sample.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.data.base import DatasetRegistry
from app.data.models import MultimodalScreeningResult
from app.services.pipeline import run_screening_pipeline
from app.services.firebase_service import FirestoreRepository

router = APIRouter()


class ScreeningRequest(BaseModel):
    sample_id: str
    dataset: str = "synthetic"
    enable_ocr: bool = False
    enable_mrz: bool = False
    enable_visual_forensics: bool = False
    enable_biometric_verification: bool = False
    enable_cross_document_consistency: bool = False
    enable_evidence_fusion: bool = False


@router.post("/screenings/run", response_model=MultimodalScreeningResult)
async def run_screening(request: ScreeningRequest):
    """
    Runs the end-to-end screening pipeline for a named canonical document sample.
    Returns the full MultimodalScreeningResult including evidence signals,
    conflicts, risk/uncertainty scores, and cautious decision-support recommendation.
    """
    adapter = DatasetRegistry.get(request.dataset)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{request.dataset}' not found. Available: {DatasetRegistry.list_datasets()}"
        )

    sample = adapter.get_sample(request.sample_id)
    if not sample:
        sample = adapter.get_sample_by_case_type(request.sample_id)
    if not sample:
        raise HTTPException(
            status_code=404,
            detail=f"Sample '{request.sample_id}' not found in dataset '{request.dataset}'."
        )

    result = run_screening_pipeline(
        sample,
        enable_ocr=request.enable_ocr,
        enable_mrz=request.enable_mrz,
        enable_visual_forensics=request.enable_visual_forensics,
        enable_biometric_verification=request.enable_biometric_verification,
        enable_cross_document_consistency=request.enable_cross_document_consistency,
        enable_evidence_fusion=request.enable_evidence_fusion,
    )

    # Persist to Firestore or local fallback
    FirestoreRepository.save_screening(result.screening_id, result.model_dump())

    return result
