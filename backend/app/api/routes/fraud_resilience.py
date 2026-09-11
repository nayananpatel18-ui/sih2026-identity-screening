"""Opt-in M12 synthetic resilience-lab API; separate from officer screening."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.fraud_resilience import FraudResilienceService

router = APIRouter()


class FraudResilienceRequest(BaseModel):
    scenario_id: str | None = None
    evaluate_all: bool = False


@router.get("/fraud-resilience/scenarios")
async def list_scenarios():
    return {"scenarios": FraudResilienceService().list_scenarios()}


@router.post("/fraud-resilience/evaluate")
async def evaluate(request: FraudResilienceRequest):
    service = FraudResilienceService()
    if request.evaluate_all:
        return service.evaluate_all()
    if not request.scenario_id:
        raise HTTPException(status_code=422, detail="scenario_id is required unless evaluate_all is true.")
    try:
        return service.evaluate(request.scenario_id).to_dict()
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
