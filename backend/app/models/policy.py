from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class DecisionPolicy(Base):
    __tablename__ = "decision_policies"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False)
    # Example parameters:
    # {
    #   "supplier_reliability_weight": 0.25,
    #   "lead_time_weight": 0.35,
    #   "unit_price_weight": 0.40,
    #   "min_supplier_reliability_threshold": 0.85,
    #   "safety_stock_buffer_ratio": 1.2,
    #   "max_transfer_distance_km": 1500,
    #   "expedite_cost_multiplier": 1.4
    # }
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiments = relationship("ExperimentRun", back_populates="policy")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("decision_policies.id"), nullable=True)
    policy_version = Column(String(50), nullable=False)
    benchmark_suite = Column(String(100), default="STANDARD_SUPPLY_CHAIN_BENCHMARK")
    scenarios_evaluated = Column(JSON, default=list)  # List of evaluated scenarios
    baseline_metrics = Column(JSON, nullable=False)
    # {
    #   "avg_recovery_cost": 18450.0,
    #   "total_stockout_units": 140,
    #   "orders_protected_pct": 82.5,
    #   "avg_lead_time_days": 8.2,
    #   "sla_compliance_rate": 0.88
    # }
    candidate_metrics = Column(JSON, nullable=False)
    # {
    #   "avg_recovery_cost": 16900.0,
    #   "total_stockout_units": 45,
    #   "orders_protected_pct": 96.0,
    #   "avg_lead_time_days": 5.4,
    #   "sla_compliance_rate": 0.95
    # }
    comparison_summary = Column(JSON, nullable=False)
    # {
    #   "cost_reduction_pct": 8.4,
    #   "stockout_reduction_pct": 67.8,
    #   "sla_improvement_pct": 7.0,
    #   "passes_safety_gate": true,
    #   "regression_detected": false
    # }
    is_promoted = Column(Boolean, default=False)
    evaluation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    policy = relationship("DecisionPolicy", back_populates="experiments")
