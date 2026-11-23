from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WorkflowCreate(BaseModel):
    objective: str = Field(..., description="Natural language operational objective")
    scenario_key: Optional[str] = Field(None, description="Preset scenario key e.g. 'SUPPLIER_DELAY_APEX'")
    auto_execute_low_risk: bool = Field(False, description="Whether to auto-execute low-risk actions")

class AgentTraceOut(BaseModel):
    id: int
    workflow_id: int
    agent_name: str
    task: str
    status: str
    input_state: Dict[str, Any] = {}
    output_state: Dict[str, Any] = {}
    tool_calls: List[Dict[str, Any]] = []
    duration_ms: float
    token_usage: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ActionExecutionOut(BaseModel):
    id: int
    workflow_id: int
    plan_id: Optional[int] = None
    action_type: str
    description: str
    payload: Dict[str, Any] = {}
    status: str
    requires_approval: bool
    risk_tier: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class RecoveryPlanOut(BaseModel):
    id: int
    workflow_id: int
    strategy_name: str
    strategy_type: str
    description: str
    total_recovery_cost: float
    stockout_risk_score: float
    orders_protected: int
    service_level: float
    actions: List[Dict[str, Any]] = []
    is_recommended: bool
    status: str
    action_records: List[ActionExecutionOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowOut(BaseModel):
    id: int
    title: str
    objective: str
    status: str
    scenario_key: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_cost: float
    summary: Optional[str] = None
    risk_level: str
    created_at: datetime
    traces: List[AgentTraceOut] = []
    recovery_plans: List[RecoveryPlanOut] = []
    action_executions: List[ActionExecutionOut] = []

    class Config:
        from_attributes = True

class ApprovalRequest(BaseModel):
    action_id: int
    approved: bool
    reviewer_name: str = "Operations Lead"
    notes: Optional[str] = None
