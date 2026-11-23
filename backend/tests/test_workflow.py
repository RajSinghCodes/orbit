import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.data.seed_data import seed_database
from app.models.workflow import Workflow, RecoveryPlan, ActionExecution
from app.orchestration.graph import build_orbit_workflow_graph
from app.agents.state import OrbitWorkflowState
from app.agents.execution import ExecutionAgent
from app.agents.improvement import ImprovementAgent

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_database(db)
    yield db
    db.close()

def test_full_langgraph_disruption_workflow(test_db):
    """
    End-to-End Test:
    Triggers supplier disruption workflow through compiled LangGraph.
    Verifies that all 7 agent stages execute, traces are logged, and 3 recovery strategies are generated.
    """
    # 1. Create Workflow
    wf = Workflow(
        title="Test Investigation: Apex Disruption",
        objective="Investigate supplier disruption, evaluate impact, and optimize recovery plan.",
        status="RUNNING"
    )
    test_db.add(wf)
    test_db.commit()
    test_db.refresh(wf)

    # 2. Invoke LangGraph
    initial_state: OrbitWorkflowState = {
        "workflow_id": wf.id,
        "objective": wf.objective,
        "status": "RUNNING"
    }

    graph = build_orbit_workflow_graph(test_db)
    final_state = graph.invoke(initial_state)

    # 3. Assertions
    assert final_state["completed"] is True
    assert final_state["status"] == "REQUIRES_APPROVAL"
    assert "disruption_data" in final_state
    assert final_state["disruption_data"]["delay_days"] == 7
    assert "impact_data" in final_state
    assert final_state["impact_data"]["severity"] == "CRITICAL"
    assert "forecast_data" in final_state
    assert "supplier_intel" in final_state
    assert len(final_state["supplier_intel"]) > 0
    assert "optimized_plans" in final_state
    assert len(final_state["optimized_plans"]) == 3
    assert final_state["verification_report"]["is_verified"] is True

    # 4. Verify Recovery Plans persisted to DB
    plans = test_db.query(RecoveryPlan).filter(RecoveryPlan.workflow_id == wf.id).all()
    assert len(plans) == 3

    # Check that recommended plan is Balanced Transfer & Sourcing
    rec_plan = [p for p in plans if p.is_recommended][0]
    assert rec_plan.strategy_type == "BALANCED_TRANSFER_PURCHASE"

    # 5. Test Action Approval & Simulated Execution
    pending_actions = test_db.query(ActionExecution).filter(
        ActionExecution.workflow_id == wf.id
    ).all()
    assert len(pending_actions) > 0

    # Approve all actions
    for a in pending_actions:
        a.status = "APPROVED"
        a.approved_by = "Lead Operations Reviewer"
    test_db.commit()

    # Execute approved actions
    receipts = ExecutionAgent.execute_approved_actions(
        db=test_db,
        workflow_id=wf.id,
        action_ids=[a.id for a in pending_actions]
    )
    assert len(receipts) == len(pending_actions)

def test_self_improvement_experiment_and_promotion(test_db):
    """
    Tests the Self-Improvement Engine:
    Runs benchmark experiment with candidate policy, checks safety gates, and executes promotion.
    """
    cand_params = {
        "supplier_reliability_weight": 0.45,
        "lead_time_weight": 0.35,
        "unit_price_weight": 0.20,
        "min_supplier_reliability_threshold": 0.90,
        "safety_stock_buffer_ratio": 1.30
    }

    result = ImprovementAgent.run_benchmark_experiment(
        db=test_db,
        candidate_version="v1.1.0-test-candidate",
        candidate_params=cand_params
    )

    assert "experiment_id" in result
    assert result["comparison_summary"]["stockout_reduction_pct"] > 50.0
    assert result["comparison_summary"]["passes_safety_gate"] is True

    # Test promotion
    promo_result = ImprovementAgent.promote_policy(
        db=test_db,
        experiment_id=result["experiment_id"],
        approved_by="VP of Global Supply Chain"
    )
    assert promo_result["status"] == "ACTIVE_PRODUCTION"
    assert promo_result["promoted_version"] == "v1.1.0-test-candidate"

    # Test rollback
    rollback_result = ImprovementAgent.rollback_to_baseline(test_db, target_version="v1.0.0-baseline")
    assert rollback_result["status"] == "ROLLED_BACK"
    assert rollback_result["active_version"] == "v1.0.0-baseline"
