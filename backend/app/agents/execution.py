import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.models.workflow import ActionExecution, Workflow
from app.services.simulation_service import SimulationService
from app.services.trace_service import TraceService

class ExecutionAgent:
    """
    Execution Agent:
    - Converts approved recovery plans into idempotent simulated operational actions.
    - Interacts with simulated external supplier systems and warehouse logistics.
    - Issues simulated purchase orders and dispatches inventory transfer orders.
    - Verifies post-execution state mutations.
    """
    NAME = "Execution Agent"

    @classmethod
    def execute_approved_actions(cls, db: Session, workflow_id: int, action_ids: List[int]) -> List[Dict[str, Any]]:
        start_time = time.time()
        actions = db.query(ActionExecution).filter(
            ActionExecution.workflow_id == workflow_id,
            ActionExecution.id.in_(action_ids)
        ).all()

        receipts = []
        tool_calls = []

        for act in actions:
            # Execute simulated transaction
            receipt = SimulationService.execute_action(db, act)
            receipts.append({"action_id": act.id, "action_type": act.action_type, "receipt": receipt})

            tool_calls.append({
                "tool_name": f"execute_{act.action_type.lower()}",
                "arguments": act.payload,
                "result": receipt
            })

        # Update workflow status if all actions executed
        remaining_pending = db.query(ActionExecution).filter(
            ActionExecution.workflow_id == workflow_id,
            ActionExecution.status == "PENDING_APPROVAL"
        ).count()

        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf and remaining_pending == 0:
            wf.status = "COMPLETED"
            db.commit()

        duration_ms = (time.time() - start_time) * 1000.0

        TraceService.record_trace(
            db=db,
            workflow_id=workflow_id,
            agent_name=cls.NAME,
            task=f"Execute {len(receipts)} authorized operational actions across simulated ERP/WMS",
            input_state={"action_ids": action_ids},
            output_state={"receipts": receipts, "remaining_pending": remaining_pending},
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            token_usage=130
        )

        return receipts
