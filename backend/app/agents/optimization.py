import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.models.workflow import RecoveryPlan, ActionExecution
from app.models.policy import DecisionPolicy
from app.services.optimization_service import OptimizationService
from app.services.trace_service import TraceService

class OptimizationAgent:
    """
    Optimization Agent:
    - Generates 3 feasible, constraint-aware recovery strategies.
    - Evaluates total cost, stockout risk score, orders protected, and expected SLA.
    - Persists recovery plans and pending action executions for human review.
    """
    NAME = "Optimization Agent"

    @classmethod
    def execute(cls, state: OrbitWorkflowState, db: Session) -> Dict[str, Any]:
        start_time = time.time()
        workflow_id = state.get("workflow_id", 1)
        disruption = state.get("disruption_data", {})
        impact = state.get("impact_data", {})

        prod_id = disruption.get("affected_product_id", 1)
        wh_id = disruption.get("affected_warehouse_id", 1)
        sup_id = disruption.get("disrupted_supplier_id", 1)
        shortfall = impact.get("shortfall_units", 60)
        delay_days = disruption.get("delay_days", 7)

        # Retrieve active decision policy
        active_policy = db.query(DecisionPolicy).filter(DecisionPolicy.is_active == True).first()
        policy_params = active_policy.parameters if active_policy else None

        # Formulate strategies deterministically
        strategies = OptimizationService.formulate_recovery_strategies(
            db=db,
            disrupted_supplier_id=sup_id,
            affected_product_id=prod_id,
            affected_warehouse_id=wh_id,
            shortfall_qty=shortfall,
            disruption_days=delay_days,
            policy_params=policy_params
        )

        recommended_plan = None
        persisted_plans = []

        # Persist plans and actions to DB
        for s in strategies:
            is_feasible = s.get("is_feasible", True)
            plan_status = "PROPOSED" if is_feasible else "REJECTED_INFEASIBLE"
            
            plan = RecoveryPlan(
                workflow_id=workflow_id,
                strategy_name=s["strategy_name"],
                strategy_type=s["strategy_type"],
                description=s["description"],
                total_recovery_cost=s["total_recovery_cost"],
                stockout_risk_score=s["stockout_risk_score"],
                orders_protected=s["orders_protected"],
                service_level=s["service_level"],
                actions=s["actions"],
                is_recommended=s["is_recommended"] and is_feasible,
                status=plan_status
            )
            db.add(plan)
            db.flush()

            # Create action execution items only for feasible plans
            if is_feasible:
                for act in s["actions"]:
                    action_rec = ActionExecution(
                        workflow_id=workflow_id,
                        plan_id=plan.id,
                        action_type=act["action_type"],
                        description=act["description"],
                        payload=act.get("payload", {}),
                        status="PENDING_APPROVAL" if act.get("requires_approval", True) else "APPROVED",
                        requires_approval=act.get("requires_approval", True),
                        risk_tier=act.get("risk_tier", "REQUIRES_APPROVAL")
                    )
                    db.add(action_rec)

            persisted_plans.append({**s, "id": plan.id, "status": plan_status})
            if s["is_recommended"] and is_feasible:
                recommended_plan = {**s, "id": plan.id, "status": plan_status}

        db.commit()

        tool_calls = [
            {
                "tool_name": "optimize_recovery_strategies",
                "arguments": {
                    "product_id": prod_id,
                    "warehouse_id": wh_id,
                    "shortfall": shortfall,
                    "strategies_evaluated": len(strategies)
                },
                "result": {
                    "generated_plans_count": len(strategies),
                    "recommended_strategy": recommended_plan["strategy_name"] if recommended_plan else "None"
                }
            }
        ]

        duration_ms = (time.time() - start_time) * 1000.0

        TraceService.record_trace(
            db=db,
            workflow_id=workflow_id,
            agent_name=cls.NAME,
            task="Evaluate multi-objective trade-offs and formulate competing recovery plans",
            input_state={"shortfall_units": shortfall, "disruption_days": delay_days},
            output_state={
                "optimized_plans_count": len(persisted_plans),
                "recommended_plan": recommended_plan
            },
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            token_usage=285
        )

        return {
            "optimized_plans": persisted_plans,
            "recommended_plan": recommended_plan,
            "current_step": "Verification Agent Dispatched"
        }
