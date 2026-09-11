"""
Health and Status API Route.
"""

from fastapi import APIRouter
from app.services.firebase_service import FirestoreRepository
from app.data.base import DatasetRegistry
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return backend status, timestamp, dataset provider, and database state."""
    return {
        "status": "online",
        "service": "SIH 2026 AI-Powered Identity Screening Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "firebase_connected": FirestoreRepository.is_connected(),
        "active_datasets": DatasetRegistry.list_datasets(),
        "version": "1.0.0"
    }
