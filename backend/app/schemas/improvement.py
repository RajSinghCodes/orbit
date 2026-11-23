from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DecisionPolicyBase(BaseModel):
    version: str
    name: str
    description: str
    parameters: Dict[str, Any]
    is_active: bool = False

class DecisionPolicyCreate(BaseModel):
    version: str
    name: str
    description: str
    parameters: Dict[str, Any]

class DecisionPolicyOut(DecisionPolicyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ExperimentRunOut(BaseModel):
    id: int
    policy_id: Optional[int] = None
    policy_version: str
    benchmark_suite: str
    scenarios_evaluated: List[str] = []
    baseline_metrics: Dict[str, Any]
    candidate_metrics: Dict[str, Any]
    comparison_summary: Dict[str, Any]
    is_promoted: bool
    evaluation_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExperimentRequest(BaseModel):
    candidate_version: str = "v1.2.0-dynamic-reliability"
    candidate_parameters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "supplier_reliability_weight": 0.45,
            "lead_time_weight": 0.35,
            "unit_price_weight": 0.20,
            "min_supplier_reliability_threshold": 0.90,
            "safety_stock_buffer_ratio": 1.35,
            "expedite_cost_multiplier": 1.25,
            "transfer_cost_per_unit_km": 0.08
        }
    )
    benchmark_suite: str = "STANDARD_SUPPLY_CHAIN_BENCHMARK"

class PromotionRequest(BaseModel):
    experiment_id: int
    approved_by: str = "Chief Operations Officer"
    notes: Optional[str] = None
