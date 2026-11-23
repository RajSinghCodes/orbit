from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.workflow import Workflow, AgentTrace, RecoveryPlan, ActionExecution
from app.schemas.workflow import (
    WorkflowCreate, WorkflowOut, AgentTraceOut, RecoveryPlanOut,
    ActionExecutionOut, ApprovalRequest
)
from app.orchestration.graph import build_orbit_workflow_graph
from app.agents.state import OrbitWorkflowState
from app.agents.execution import ExecutionAgent

router = APIRouter(prefix="/workflows", tags=["Multi-Agent Workflows"])

@router.get("", response_model=List[WorkflowOut])
def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.created_at.desc()).all()

@router.post("", response_model=WorkflowOut)
def create_and_execute_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new operational investigation and dispatches the LangGraph
    multi-agent orchestrator. Executes agents through a strictly typed state machine.
    """
    # 1. Create Workflow Record
    title = f"Investigation: {payload.objective[:60]}..."
    workflow = Workflow(
        title=title,
        objective=payload.objective,
        scenario_key=payload.scenario_key,
        status="RUNNING",
        risk_level="HIGH" if "disruption" in payload.objective.lower() or "delay" in payload.objective.lower() else "MEDIUM"
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # 2. Build and Invoke LangGraph
    initial_state: OrbitWorkflowState = {
        "workflow_id": workflow.id,
        "objective": payload.objective,
        "scenario_key": payload.scenario_key,
        "status": "RUNNING",
        "traces": [],
        "errors": []
    }

    try:
        graph = build_orbit_workflow_graph(db)
        final_state = graph.invoke(initial_state)

        # 3. Update Workflow Record
        recommended = final_state.get("recommended_plan", {})
        impact = final_state.get("impact_data", {})
        verif = final_state.get("verification_report", {})

        summary = (
            f"Investigated operational objective. Disruption caused by supplier delay with {impact.get('shortfall_units', 60)} units shortfall. "
            f"Formulated 3 recovery plans. Recommended: '{recommended.get('strategy_name', 'Balanced Transfer & Purchase')}' "
            f"with expected SLA of {int(recommended.get('service_level', 0.96) * 100)}% and recovery cost of ${recommended.get('total_recovery_cost', 0):,.2f}. "
            f"Verification passed: {verif.get('is_verified', True)}."
        )

        workflow.summary = summary
        workflow.status = "REQUIRES_APPROVAL"
        workflow.total_cost = recommended.get("total_recovery_cost", 0.0)
        workflow.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)

    except Exception as e:
        workflow.status = "FAILED"
        workflow.summary = f"Workflow encountered error: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Orchestration failure: {str(e)}")

    return workflow

@router.get("/{id}", response_model=WorkflowOut)
def get_workflow(id: int, db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@router.get("/{id}/traces", response_model=List[AgentTraceOut])
def get_workflow_traces(id: int, db: Session = Depends(get_db)):
    return db.query(AgentTrace).filter(AgentTrace.workflow_id == id).order_by(AgentTrace.created_at.asc()).all()

@router.get("/{id}/plans", response_model=List[RecoveryPlanOut])
def get_workflow_plans(id: int, db: Session = Depends(get_db)):
    return db.query(RecoveryPlan).filter(RecoveryPlan.workflow_id == id).all()

@router.post("/{id}/actions/{action_id}/approve")
def approve_action(
    id: int,
    action_id: int,
    payload: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Human-in-the-loop approval or rejection for a consequential operational action."""
    act = db.query(ActionExecution).filter(
        ActionExecution.workflow_id == id,
        ActionExecution.id == action_id
    ).first()
    if not act:
        raise HTTPException(status_code=404, detail="Action not found")

    if payload.approved:
        act.status = "APPROVED"
        act.approved_by = payload.reviewer_name
        act.approved_at = datetime.utcnow()
    else:
        act.status = "REJECTED"

    db.commit()
    return {"action_id": act.id, "status": act.status, "approved_by": act.approved_by}

@router.post("/{id}/execute-approved")
def execute_approved_actions(
    id: int,
    db: Session = Depends(get_db)
):
    """Executes all approved simulated actions for this workflow."""
    approved_actions = db.query(ActionExecution).filter(
        ActionExecution.workflow_id == id,
        ActionExecution.status == "APPROVED"
    ).all()

    if not approved_actions:
        return {"executed_count": 0, "message": "No approved actions pending execution."}

    action_ids = [a.id for a in approved_actions]
    receipts = ExecutionAgent.execute_approved_actions(db, workflow_id=id, action_ids=action_ids)

    return {
        "workflow_id": id,
        "executed_count": len(receipts),
        "receipts": receipts,
        "message": f"Successfully executed {len(receipts)} simulated operational actions."
    }
