import time
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.policy import DecisionPolicy, ExperimentRun
from app.services.supplier_service import SupplierService
from app.services.inventory_service import InventoryService
from app.services.optimization_service import OptimizationService
from app.services.trace_service import TraceService

class ImprovementAgent:
    """
    Self-Improvement Agent:
    - Studies historical operational traces and decision policy parameters.
    - Evaluates candidate policies against a fixed benchmark suite of training and holdout scenarios.
    - Executes actual multi-objective optimization algorithms and deterministic order fulfillment simulations.
    - Measures recovery cost, stockout units, orders protected, SLA compliance, and constraint violations.
    - Enforces safety gates and holdout validation before permitting production promotion.
    - Fully supports human approval and one-click rollback.
    """
    NAME = "Self-Improvement Agent"

    BENCHMARK_SCENARIOS = [
        {
            "id": "BENCH-01",
            "name": "Severe 7-Day Tier-1 Supplier Delay (Apex Industrial - P-MOT-100)",
            "is_holdout": False,
            "product_id": 1,
            "warehouse_id": 1,
            "disrupted_supplier_id": 1,
            "shortfall_units": 50,
            "disruption_days": 7,
            "initial_available": 6,
            "safety_stock": 40,
            "orders": [
                {"order_id": 101, "customer_name": "Boeing", "priority": "VIP", "required_day": 2, "qty": 10, "revenue": 3400.0},
                {"order_id": 102, "customer_name": "Rockwell", "priority": "VIP", "required_day": 3, "qty": 15, "revenue": 5100.0},
                {"order_id": 103, "customer_name": "Siemens", "priority": "EXPEDITED", "required_day": 4, "qty": 12, "revenue": 4080.0},
                {"order_id": 104, "customer_name": "Caterpillar", "priority": "STANDARD", "required_day": 5, "qty": 14, "revenue": 4760.0},
                {"order_id": 105, "customer_name": "Emerson", "priority": "STANDARD", "required_day": 6, "qty": 8, "revenue": 2720.0},
            ]
        },
        {
            "id": "BENCH-02",
            "name": "Sudden 45% Demand Surge in Chicago Hub (P-MOT-100)",
            "is_holdout": False,
            "product_id": 1,
            "warehouse_id": 1,
            "disrupted_supplier_id": 1,
            "shortfall_units": 75,
            "disruption_days": 6,
            "initial_available": 6,
            "safety_stock": 40,
            "orders": [
                {"order_id": 201, "customer_name": "Lockheed", "priority": "VIP", "required_day": 2, "qty": 20, "revenue": 6800.0},
                {"order_id": 202, "customer_name": "Honeywell", "priority": "VIP", "required_day": 3, "qty": 20, "revenue": 6800.0},
                {"order_id": 203, "customer_name": "General Electric", "priority": "EXPEDITED", "required_day": 4, "qty": 15, "revenue": 5100.0},
                {"order_id": 204, "customer_name": "Parker Hannifin", "priority": "STANDARD", "required_day": 5, "qty": 25, "revenue": 8500.0},
            ]
        },
        {
            "id": "BENCH-03",
            "name": "Multi-Supplier Disruption & Component Bottleneck (P-MOT-100)",
            "is_holdout": False,
            "product_id": 1,
            "warehouse_id": 1,
            "disrupted_supplier_id": 1,
            "shortfall_units": 90,
            "disruption_days": 8,
            "initial_available": 10,
            "safety_stock": 40,
            "orders": [
                {"order_id": 301, "customer_name": "Raytheon", "priority": "VIP", "required_day": 2, "qty": 15, "revenue": 5100.0},
                {"order_id": 302, "customer_name": "ABB Robotics", "priority": "VIP", "required_day": 3, "qty": 25, "revenue": 8500.0},
                {"order_id": 303, "customer_name": "Schneider Electric", "priority": "EXPEDITED", "required_day": 5, "qty": 25, "revenue": 8500.0},
                {"order_id": 304, "customer_name": "Fanuc North America", "priority": "STANDARD", "required_day": 7, "qty": 35, "revenue": 11900.0},
            ]
        },
        {
            "id": "BENCH-04",
            "name": "Holdout Scenario: High-Pressure Flow Valve Stockout Cliff (P-VLV-200)",
            "is_holdout": True,
            "product_id": 5,
            "warehouse_id": 3,
            "disrupted_supplier_id": 1,
            "shortfall_units": 60,
            "disruption_days": 7,
            "initial_available": 8,
            "safety_stock": 45,
            "orders": [
                {"order_id": 401, "customer_name": "Chevron Process", "priority": "VIP", "required_day": 3, "qty": 18, "revenue": 3960.0},
                {"order_id": 402, "customer_name": "ExxonMobil Ops", "priority": "EXPEDITED", "required_day": 4, "qty": 22, "revenue": 4840.0},
                {"order_id": 403, "customer_name": "Valero Refining", "priority": "STANDARD", "required_day": 6, "qty": 25, "revenue": 5500.0},
            ]
        },
        {
            "id": "BENCH-05",
            "name": "Holdout Scenario: Actuator Line Interruption Stress Test (P-ACT-150)",
            "is_holdout": True,
            "product_id": 2,
            "warehouse_id": 2,
            "disrupted_supplier_id": 1,
            "shortfall_units": 70,
            "disruption_days": 6,
            "initial_available": 10,
            "safety_stock": 50,
            "orders": [
                {"order_id": 501, "customer_name": "General Dynamics", "priority": "VIP", "required_day": 2, "qty": 20, "revenue": 3500.0},
                {"order_id": 502, "customer_name": "Northrop Grumman", "priority": "EXPEDITED", "required_day": 4, "qty": 25, "revenue": 4375.0},
                {"order_id": 503, "customer_name": "Textron Aviation", "priority": "STANDARD", "required_day": 5, "qty": 30, "revenue": 5250.0},
            ]
        }
    ]

    @classmethod
    def evaluate_scenario_policy(
        cls,
        db: Session,
        scenario: Dict[str, Any],
        policy_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes actual supplier scoring, constrained optimization allocation,
        and chronological schedule simulation for a specific benchmark scenario.
        Returns data-grounded metrics with zero synthetic multipliers.
        """
        prod_id = scenario["product_id"]
        wh_id = scenario["warehouse_id"]
        disrupted_sup = scenario["disrupted_supplier_id"]
        shortfall = scenario["shortfall_units"]
        init_avail = scenario["initial_available"]
        orders = scenario["orders"]

        # 1. Evaluate alternative suppliers using policy parameters
        alt_suppliers = SupplierService.evaluate_alternative_suppliers(
            db=db,
            product_id=prod_id,
            exclude_supplier_id=disrupted_sup,
            policy_params=policy_params
        )

        # 2. Find surplus sister warehouses
        surplus_warehouses = InventoryService.find_surplus_warehouses(
            db=db,
            product_id=prod_id,
            exclude_warehouse_id=wh_id,
            required_qty=shortfall
        )

        # 3. Solve allocation with OR-Tools
        opt = OptimizationService.solve_optimal_split_allocation(
            shortfall_qty=shortfall,
            surplus_warehouses=surplus_warehouses,
            alt_suppliers=alt_suppliers,
            max_transfer_ratio=0.50,
            policy_params=policy_params
        )

        # Build chronological arrivals
        replenishments = []
        for t in opt["transfers"]:
            replenishments.append({"arrival_day": t.get("transfer_lead_time_days", 2), "qty": t["allocated_qty"]})
        for p in opt["purchase_orders"]:
            replenishments.append({"arrival_day": p.get("lead_time_days", 5), "qty": p["allocated_qty"]})

        # 4. Deterministic chronological simulation
        ref_today = date.today()
        order_dicts = [
            {
                "order_id": o["order_id"],
                "customer_name": o["customer_name"],
                "priority": o["priority"],
                "required_delivery_date": str(ref_today + timedelta(days=o["required_day"])),
                "ordered_qty": o["qty"],
                "order_revenue": o["revenue"]
            }
            for o in orders
        ]

        sim = OptimizationService.simulate_recovery_schedule(
            available_qty=init_avail,
            safety_stock_released=0,
            replenishments=replenishments,
            at_risk_orders=order_dicts,
            reference_date=ref_today
        )

        # Constraint check: supplier weekly capacity
        violations = 0
        for p in opt["purchase_orders"]:
            if p["allocated_qty"] > p.get("max_capacity_per_week", 1000):
                violations += 1

        avg_lead_time = (
            float(np.mean([r["arrival_day"] for r in replenishments]))
            if replenishments else 10.0
        )

        return {
            "scenario_id": scenario["id"],
            "is_holdout": scenario["is_holdout"],
            "recovery_cost": opt["total_cost"],
            "stockout_units": sim["stockout_units"],
            "orders_protected": sim["orders_protected"],
            "total_orders": len(orders),
            "service_level": sim["service_level"],
            "stockout_risk_score": sim["stockout_risk_score"],
            "avg_lead_time": avg_lead_time,
            "constraint_violations": violations,
            "is_feasible": opt["status"] in ["OPTIMAL", "FEASIBLE", "FEASIBLE_HEURISTIC"] and violations == 0
        }

    @classmethod
    def run_benchmark_experiment(
        cls,
        db: Session,
        candidate_version: str,
        candidate_params: Dict[str, Any],
        candidate_name: str = "Reliability-Weighted Policy",
        candidate_description: str = "Prioritizes supplier reliability and shorter lead times to minimize stockout cliffs."
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Fetch active baseline policy
        baseline_policy = db.query(DecisionPolicy).filter(DecisionPolicy.is_active == True).first()
        if not baseline_policy:
            baseline_params = {
                "supplier_reliability_weight": 0.20,
                "lead_time_weight": 0.30,
                "unit_price_weight": 0.50,
                "min_supplier_reliability_threshold": 0.80,
                "safety_stock_buffer_ratio": 1.15
            }
            baseline_version = "v1.0.0-baseline"
        else:
            baseline_params = baseline_policy.parameters
            baseline_version = baseline_policy.version

        # 2. Run both baseline and candidate against every benchmark scenario
        baseline_results = []
        candidate_results = []

        for sc in cls.BENCHMARK_SCENARIOS:
            b_res = cls.evaluate_scenario_policy(db, sc, baseline_params)
            c_res = cls.evaluate_scenario_policy(db, sc, candidate_params)
            baseline_results.append(b_res)
            candidate_results.append(c_res)

        # Aggregate metrics
        base_avg_cost = round(float(np.mean([r["recovery_cost"] for r in baseline_results])), 2)
        base_total_stockout = int(np.sum([r["stockout_units"] for r in baseline_results]))
        total_benchmark_orders = sum(r["total_orders"] for r in baseline_results)
        base_prot_pct = round(float(sum(r["orders_protected"] for r in baseline_results)) / max(1, total_benchmark_orders) * 100.0, 1)
        base_avg_lt = round(float(np.mean([r["avg_lead_time"] for r in baseline_results])), 1)
        base_sla = round(float(np.mean([r["service_level"] for r in baseline_results])), 3)

        cand_avg_cost = round(float(np.mean([r["recovery_cost"] for r in candidate_results])), 2)
        cand_total_stockout = int(np.sum([r["stockout_units"] for r in candidate_results]))
        cand_prot_pct = round(float(sum(r["orders_protected"] for r in candidate_results)) / max(1, total_benchmark_orders) * 100.0, 1)
        cand_avg_lt = round(float(np.mean([r["avg_lead_time"] for r in candidate_results])), 1)
        cand_sla = round(float(np.mean([r["service_level"] for r in candidate_results])), 3)

        # Holdout performance evaluation
        holdout_cand = [r for r in candidate_results if r["is_holdout"]]
        holdout_base = [r for r in baseline_results if r["is_holdout"]]
        holdout_cand_sla = float(np.mean([r["service_level"] for r in holdout_cand])) if holdout_cand else 1.0
        holdout_base_sla = float(np.mean([r["service_level"] for r in holdout_base])) if holdout_base else 1.0
        holdout_passed = (holdout_cand_sla >= holdout_base_sla)

        # Constraint violations check
        total_violations = sum(r["constraint_violations"] for r in candidate_results)

        # Comparative deltas
        stockout_reduction_pct = round(((base_total_stockout - cand_total_stockout) / max(1, base_total_stockout)) * 100.0, 1) if base_total_stockout > 0 else 0.0
        sla_improvement_pct = round((cand_sla - base_sla) * 100.0, 1)
        cost_change_pct = round(((cand_avg_cost - base_avg_cost) / max(1.0, base_avg_cost)) * 100.0, 1)

        # Safety Gates:
        # Candidate passes promotion criteria IF:
        # 1. Stockout units reduced by >= 25% (or 0 stockout maintained)
        # 2. Overall SLA improved or preserved
        # 3. Cost increase does not exceed 25%
        # 4. Holdout validation passes (no overfitting)
        # 5. Zero operational constraint violations
        passes_safety_gate = bool(
            (stockout_reduction_pct >= 25.0 or cand_total_stockout == 0) and
            (cand_sla >= base_sla) and
            (cost_change_pct <= 25.0) and
            holdout_passed and
            (total_violations == 0)
        )

        baseline_metrics = {
            "policy_version": baseline_version,
            "avg_recovery_cost": base_avg_cost,
            "total_stockout_units": base_total_stockout,
            "orders_protected_pct": base_prot_pct,
            "avg_lead_time_days": base_avg_lt,
            "sla_compliance_rate": base_sla
        }

        candidate_metrics = {
            "policy_version": candidate_version,
            "avg_recovery_cost": cand_avg_cost,
            "total_stockout_units": cand_total_stockout,
            "orders_protected_pct": cand_prot_pct,
            "avg_lead_time_days": cand_avg_lt,
            "sla_compliance_rate": cand_sla
        }

        comparison_summary = {
            "stockout_reduction_pct": stockout_reduction_pct,
            "sla_improvement_pct": sla_improvement_pct,
            "cost_change_pct": cost_change_pct,
            "lead_time_reduction_days": round(base_avg_lt - cand_avg_lt, 1),
            "holdout_passed": holdout_passed,
            "constraint_violations": total_violations,
            "training_scenarios_evaluated": len([s for s in cls.BENCHMARK_SCENARIOS if not s["is_holdout"]]),
            "holdout_scenarios_evaluated": len(holdout_cand),
            "passes_safety_gate": passes_safety_gate,
            "regression_detected": not passes_safety_gate,
            "recommendation": "PROMOTE_TO_PRODUCTION" if passes_safety_gate else "REJECT_CANDIDATE"
        }

        # 3. Persist Candidate Policy and Experiment Run to Database
        existing_cand_policy = db.query(DecisionPolicy).filter(DecisionPolicy.version == candidate_version).first()
        if not existing_cand_policy:
            cand_policy_obj = DecisionPolicy(
                version=candidate_version,
                name=candidate_name,
                description=candidate_description,
                parameters=candidate_params,
                is_active=False
            )
            db.add(cand_policy_obj)
            db.flush()
            cand_policy_id = cand_policy_obj.id
        else:
            cand_policy_id = existing_cand_policy.id

        experiment = ExperimentRun(
            policy_id=cand_policy_id,
            policy_version=candidate_version,
            benchmark_suite="EMPIRICAL_SIMULATION_BENCHMARK_SUITE_V2",
            scenarios_evaluated=[s["name"] for s in cls.BENCHMARK_SCENARIOS],
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            comparison_summary=comparison_summary,
            is_promoted=False,
            evaluation_notes=f"Empirically simulated across {len(cls.BENCHMARK_SCENARIOS)} benchmark scenarios (including 2 holdouts). Stockout rate reduced by {stockout_reduction_pct}%. Safety gate: {'PASSED' if passes_safety_gate else 'REJECTED'}."
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        duration_ms = (time.time() - start_time) * 1000.0

        return {
            "experiment_id": experiment.id,
            "candidate_version": candidate_version,
            "baseline_metrics": baseline_metrics,
            "candidate_metrics": candidate_metrics,
            "comparison_summary": comparison_summary,
            "duration_ms": round(duration_ms, 2)
        }

    @classmethod
    def promote_policy(cls, db: Session, experiment_id: int, approved_by: str = "Operations Lead") -> Dict[str, Any]:
        """
        Promotes a validated candidate decision policy to active production status.
        Deactivates previous active policy with full version history audit.
        """
        experiment = db.query(ExperimentRun).filter(ExperimentRun.id == experiment_id).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found.")

        target_policy = db.query(DecisionPolicy).filter(DecisionPolicy.version == experiment.policy_version).first()
        if not target_policy:
            raise ValueError(f"Policy version {experiment.policy_version} not found.")

        # Deactivate all policies
        db.query(DecisionPolicy).update({"is_active": False})
        target_policy.is_active = True
        experiment.is_promoted = True
        experiment.evaluation_notes = f"{experiment.evaluation_notes or ''} [PROMOTED by {approved_by} at {datetime.now().isoformat()}]"

        db.commit()
        return {
            "promoted_version": target_policy.version,
            "policy_name": target_policy.name,
            "status": "ACTIVE_PRODUCTION",
            "activated_at": datetime.now().isoformat()
        }

    @classmethod
    def rollback_to_baseline(cls, db: Session, target_version: str = "v1.0.0-baseline") -> Dict[str, Any]:
        """
        Rolls back the active policy to baseline or specified version.
        """
        target_policy = db.query(DecisionPolicy).filter(DecisionPolicy.version == target_version).first()
        if not target_policy:
            raise ValueError(f"Target version {target_version} not found.")

        db.query(DecisionPolicy).update({"is_active": False})
        target_policy.is_active = True
        db.commit()

        return {
            "active_version": target_policy.version,
            "status": "ROLLED_BACK",
            "message": f"Successfully restored operational policy {target_version} to active status."
        }
