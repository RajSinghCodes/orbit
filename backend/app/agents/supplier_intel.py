import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.models.policy import DecisionPolicy
from app.services.supplier_service import SupplierService
from app.services.trace_service import TraceService

class SupplierIntelligenceAgent:
    """
    Supplier Intelligence Agent:
    - Identifies qualified alternative suppliers for affected SKUs.
    - Evaluates lead times, unit pricing, historical OTIF reliability, and MOQ.
    - Applies active decision policy weights to rank viable options.
    """
    NAME = "Supplier Intelligence Agent"

    @classmethod
    def execute(cls, state: OrbitWorkflowState, db: Session) -> Dict[str, Any]:
        start_time = time.time()
        workflow_id = state.get("workflow_id", 1)
        disruption = state.get("disruption_data", {})

        prod_id = disruption.get("affected_product_id", 1)
        disrupted_sup_id = disruption.get("disrupted_supplier_id", 1)

        # Retrieve active decision policy parameters
        active_policy = db.query(DecisionPolicy).filter(DecisionPolicy.is_active == True).first()
        policy_params = active_policy.parameters if active_policy else None

        # Query and rank alternative suppliers
        candidates = SupplierService.evaluate_alternative_suppliers(
            db=db,
            product_id=prod_id,
            exclude_supplier_id=disrupted_sup_id,
            policy_params=policy_params
        )

        tool_calls = [
            {
                "tool_name": "query_alternative_suppliers",
                "arguments": {
                    "product_id": prod_id,
                    "exclude_supplier_id": disrupted_sup_id,
                    "policy_version": active_policy.version if active_policy else "default"
                },
                "result": {"qualified_candidates_count": len(candidates)}
            }
        ]

        duration_ms = (time.time() - start_time) * 1000.0

        TraceService.record_trace(
            db=db,
            workflow_id=workflow_id,
            agent_name=cls.NAME,
            task="Retrieve and evaluate qualified alternative suppliers via multi-attribute scoring",
            input_state={"product_id": prod_id, "disrupted_supplier_id": disrupted_sup_id},
            output_state={"supplier_intel": candidates},
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            token_usage=190
        )

        return {"supplier_intel": candidates, "current_step": "Optimization Agent Dispatched"}
