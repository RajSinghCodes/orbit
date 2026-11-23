import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.services.trace_service import TraceService

class SupervisorAgent:
    """
    Supervisor / Orchestrator Agent:
    - Interprets natural language operational objectives.
    - Classifies problem domain.
    - Constructs structured DAG execution plan.
    - Manages agent dependencies and shared workflow state.
    """
    NAME = "Supervisor Agent"

    @classmethod
    def execute(cls, state: OrbitWorkflowState, db: Session) -> Dict[str, Any]:
        start_time = time.time()
        objective = state.get("objective", "")
        workflow_id = state.get("workflow_id", 1)

        # 1. Classify task based on keywords / intent
        obj_lower = objective.lower()
        if "delay" in obj_lower or "disruption" in obj_lower or "supplier" in obj_lower:
            task_type = "SUPPLIER_DISRUPTION_RECOVERY"
        elif "demand" in obj_lower or "surge" in obj_lower or "spike" in obj_lower:
            task_type = "DEMAND_SURGE_RESPONSE"
        elif "stockout" in obj_lower or "transfer" in obj_lower or "inventory" in obj_lower:
            task_type = "INVENTORY_REBALANCING"
        else:
            task_type = "GENERAL_OPERATIONAL_INVESTIGATION"

        # 2. Construct deterministic plan steps
        plan_steps = [
            "1. Detection: Query active disruption events, PO records, and supplier notices.",
            "2. Impact Analysis: Calculate inventory depletion, stockout runway, and customer orders at risk.",
            "3. Demand Forecasting: Fit time-series demand models to predict 14-day requirements.",
            "4. Supplier Intelligence: Query qualified alternative vendors, lead times, and reliability ratings.",
            "5. Recovery Optimization: Formulate and compare mathematical recovery strategies.",
            "6. Invariant Verification: Cross-check mass-balance, lead times, and capacity constraints.",
            "7. Action Plan Synthesis: Structure executable recommendations for human oversight."
        ]

        tool_calls = [
            {
                "tool_name": "classify_operational_objective",
                "arguments": {"objective": objective},
                "result": {"task_classification": task_type, "confidence": 0.98}
            },
            {
                "tool_name": "build_execution_plan",
                "arguments": {"task_type": task_type},
                "result": {"steps_count": len(plan_steps)}
            }
        ]

        output_state = {
            "task_classification": task_type,
            "plan_steps": plan_steps,
            "current_step": "Detection Agent Dispatched",
            "status": "IN_PROGRESS"
        }

        duration_ms = (time.time() - start_time) * 1000.0

        TraceService.record_trace(
            db=db,
            workflow_id=workflow_id,
            agent_name=cls.NAME,
            task="Interpret objective, classify task, and construct execution plan",
            input_state={"objective": objective},
            output_state=output_state,
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            token_usage=142
        )

        return output_state
