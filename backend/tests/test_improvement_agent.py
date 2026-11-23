import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.data.seed_data import seed_database
from app.models.policy import DecisionPolicy, ExperimentRun
from app.agents.improvement import ImprovementAgent

@pytest.fixture
def seeded_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_database(db)
    yield db
    db.close()

def test_benchmark_experiment_passes_safety_gate_with_improved_candidate(seeded_db):
    """Verifies that an objectively superior policy passes all training and holdout safety gates."""
    cand_params = {
        "supplier_reliability_weight": 0.45,
        "lead_time_weight": 0.35,
        "unit_price_weight": 0.20,
        "min_supplier_reliability_threshold": 0.90,
        "safety_stock_buffer_ratio": 1.30
    }

    result = ImprovementAgent.run_benchmark_experiment(
        db=seeded_db,
        candidate_version="v1.1.0-speed-reliability",
        candidate_params=cand_params,
        candidate_name="Speed and Reliability Optimized Policy"
    )

    summary = result["comparison_summary"]
    assert "experiment_id" in result
    assert summary["training_scenarios_evaluated"] == 3
    assert summary["holdout_scenarios_evaluated"] == 2
    assert summary["holdout_passed"] is True
    assert summary["constraint_violations"] == 0
    assert summary["stockout_reduction_pct"] > 50.0
    assert summary["passes_safety_gate"] is True
    assert summary["recommendation"] == "PROMOTE_TO_PRODUCTION"

    # Verify persisted in database
    exp_record = seeded_db.query(ExperimentRun).filter(ExperimentRun.id == result["experiment_id"]).first()
    assert exp_record is not None
    assert exp_record.is_promoted is False
    assert exp_record.policy_version == "v1.1.0-speed-reliability"

def test_benchmark_experiment_rejects_degraded_candidate(seeded_db):
    """Verifies that a degraded policy is objectively rejected by the simulation safety gates."""
    bad_params = {
        "supplier_reliability_weight": 0.05,
        "lead_time_weight": 0.05,
        "unit_price_weight": 0.90,
        "min_supplier_reliability_threshold": 0.60,
        "safety_stock_buffer_ratio": 0.90
    }

    result = ImprovementAgent.run_benchmark_experiment(
        db=seeded_db,
        candidate_version="v0.9.0-reckless-cost",
        candidate_params=bad_params,
        candidate_name="Reckless Cost-Cutting Policy"
    )

    summary = result["comparison_summary"]
    assert summary["passes_safety_gate"] is False
    assert summary["recommendation"] == "REJECT_CANDIDATE"

    # Verify not promoted in database
    exp_record = seeded_db.query(ExperimentRun).filter(ExperimentRun.id == result["experiment_id"]).first()
    assert exp_record is not None
    assert exp_record.is_promoted is False

def test_promotion_and_rollback_audit(seeded_db):
    """Verifies human-in-the-loop promotion workflow and safe rollback mechanism."""
    cand_params = {
        "supplier_reliability_weight": 0.45,
        "lead_time_weight": 0.35,
        "unit_price_weight": 0.20,
        "min_supplier_reliability_threshold": 0.90,
        "safety_stock_buffer_ratio": 1.30
    }

    result = ImprovementAgent.run_benchmark_experiment(
        db=seeded_db,
        candidate_version="v1.1.0-promotable",
        candidate_params=cand_params
    )

    # Promote
    promo = ImprovementAgent.promote_policy(
        db=seeded_db,
        experiment_id=result["experiment_id"],
        approved_by="Chief Operating Officer"
    )
    assert promo["status"] == "ACTIVE_PRODUCTION"
    assert promo["promoted_version"] == "v1.1.0-promotable"

    # Verify active flag in DB
    active_pol = seeded_db.query(DecisionPolicy).filter(DecisionPolicy.is_active == True).first()
    assert active_pol.version == "v1.1.0-promotable"

    # Rollback to baseline
    rollback = ImprovementAgent.rollback_to_baseline(seeded_db, target_version="v1.0.0-baseline")
    assert rollback["status"] == "ROLLED_BACK"
    assert rollback["active_version"] == "v1.0.0-baseline"

    restored_pol = seeded_db.query(DecisionPolicy).filter(DecisionPolicy.is_active == True).first()
    assert restored_pol.version == "v1.0.0-baseline"
