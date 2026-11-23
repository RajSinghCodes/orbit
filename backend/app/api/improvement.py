from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.policy import DecisionPolicy, ExperimentRun
from app.schemas.improvement import (
    DecisionPolicyOut, ExperimentRunOut, ExperimentRequest, PromotionRequest
)
from app.agents.improvement import ImprovementAgent

router = APIRouter(prefix="/improvement", tags=["Self-Improvement Engine"])

@router.get("/policies", response_model=List[DecisionPolicyOut])
def list_policies(db: Session = Depends(get_db)):
    return db.query(DecisionPolicy).order_by(DecisionPolicy.created_at.desc()).all()

@router.get("/experiments", response_model=List[ExperimentRunOut])
def list_experiments(db: Session = Depends(get_db)):
    return db.query(ExperimentRun).order_by(ExperimentRun.created_at.desc()).all()

@router.post("/run-experiment", response_model=ExperimentRunOut)
def run_benchmark_experiment(
    payload: ExperimentRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a controlled benchmark experiment evaluating a candidate decision policy
    against the active baseline across fixed holdout scenarios.
    """
    result = ImprovementAgent.run_benchmark_experiment(
        db=db,
        candidate_version=payload.candidate_version,
        candidate_params=payload.candidate_parameters,
        candidate_name="Dynamic Reliability-Weighted Policy",
        candidate_description="Rebalances supplier scoring to prioritize reliability and short lead times during supply disruptions."
    )

    experiment = db.query(ExperimentRun).filter(ExperimentRun.id == result["experiment_id"]).first()
    return experiment

@router.post("/promote")
def promote_policy(
    payload: PromotionRequest,
    db: Session = Depends(get_db)
):
    """Promotes an experimentally validated policy to active production status."""
    try:
        return ImprovementAgent.promote_policy(
            db=db,
            experiment_id=payload.experiment_id,
            approved_by=payload.approved_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback")
def rollback_policy(
    target_version: str = "v1.0.0-baseline",
    db: Session = Depends(get_db)
):
    """Rolls back the active policy to baseline or designated stable version."""
    try:
        return ImprovementAgent.rollback_to_baseline(db=db, target_version=target_version)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
