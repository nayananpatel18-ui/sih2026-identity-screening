"""
Canonical Data Adapter Samples API Route.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.data.base import DatasetRegistry
from app.data.models import OfficerFacingDocumentSample

router = APIRouter()


@router.get("/samples", response_model=List[str])
async def list_dataset_samples(dataset: str = Query("synthetic", description="Name of registered dataset adapter")):
    adapter = DatasetRegistry.get(dataset)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset}' not found. Registered: {DatasetRegistry.list_datasets()}")
    return adapter.list_samples()


@router.get("/samples/{sample_id}", response_model=OfficerFacingDocumentSample)
async def get_canonical_sample(sample_id: str, dataset: str = Query("synthetic")):
    adapter = DatasetRegistry.get(dataset)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Dataset adapter '{dataset}' not found.")
    
    sample = adapter.get_sample(sample_id)
    if not sample:
        # Try lookup by case type (genuine, tampered, uncertain)
        sample = adapter.get_sample_by_case_type(sample_id)
    
    if not sample:
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found in dataset '{dataset}'.")
    # Ground truth is internal evaluation metadata and must never cross the
    # officer-facing API boundary.
    return OfficerFacingDocumentSample(**sample.model_dump(exclude={"ground_truth"}))
