from typing import TypedDict, List, Dict, Any, Optional

class OrbitWorkflowState(TypedDict, total=False):
    workflow_id: int
    objective: str
    scenario_key: Optional[str]
    task_classification: str
    plan_steps: List[str]
    current_step: str
    
    # Domain data accumulated across agents
    disruption_data: Dict[str, Any]
    impact_data: Dict[str, Any]
    forecast_data: Dict[str, Any]
    supplier_intel: List[Dict[str, Any]]
    optimized_plans: List[Dict[str, Any]]
    recommended_plan: Dict[str, Any]
    verification_report: Dict[str, Any]
    executed_actions: List[Dict[str, Any]]
    
    # Execution meta
    status: str
    traces: List[Dict[str, Any]]
    errors: List[str]
    completed: bool
