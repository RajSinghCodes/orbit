from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models.supply_chain import (
    Warehouse, Supplier, Product, Inventory, CustomerOrder,
    PurchaseOrder, POLineItem, OperationalIncident, DemandHistory
)
from app.models.workflow import Workflow, AgentTrace, RecoveryPlan, ActionExecution
from app.data.seed_data import seed_database

router = APIRouter(prefix="/scenarios", tags=["Scenario Simulator"])

AVAILABLE_SCENARIOS = [
    {
        "key": "SUPPLIER_DELAY_APEX",
        "name": "Scenario 1: Primary Supplier 7-Day Inbound Delay",
        "description": "Apex Industrial Components reports sub-tier semiconductor wafer bottleneck, delaying PO-2026-8812 (150 Servo Motors to Chicago DC) by 7 days.",
        "difficulty": "Critical",
        "recommended_objective": "Investigate the supplier disruption, identify all affected products and customer orders, estimate the business impact, and prepare the best recovery strategy while minimizing additional costs."
    },
    {
        "key": "DEMAND_SPIKE_CHICAGO",
        "name": "Scenario 2: Sudden 60% Demand Surge in Midwest DC",
        "description": "Midwest automotive OEM increases weekly demand by 60% for Servo Motors (P-MOT-100), accelerating stockout runway to less than 48 hours.",
        "difficulty": "High",
        "recommended_objective": "Analyze the sudden demand spike in Chicago, forecast updated 14-day requirements, and optimize expedited inventory rebalancing."
    },
    {
        "key": "WAREHOUSE_STOCKOUT_DALLAS",
        "name": "Scenario 3: Severe Warehouse Depletion in South Central Hub",
        "description": "Dallas Logistics Hub on-hand inventory drops unexpectedly below safety threshold, risking 6 regional VIP orders.",
        "difficulty": "Medium",
        "recommended_objective": "Audit Dallas warehouse inventory depletion, evaluate cross-dock transfers from Atlanta, and stabilize safety stock."
    },
    {
        "key": "MULTI_SUPPLIER_DISRUPTION",
        "name": "Scenario 4: Concurrent Multi-Supplier Chokepoint",
        "description": "Simultaneous delivery delays reported by both Apex Industrial (Motors) and Global Logistics (Bearings), testing multi-echelon resilience.",
        "difficulty": "Critical",
        "recommended_objective": "Coordinate recovery across multiple disrupted suppliers, prioritize critical line items, and formulate a hybrid sourcing response."
    },
    {
        "key": "RESET_BASELINE",
        "name": "Scenario 0: Reset Environment to Pristine Benchmark State",
        "description": "Restores initial clean supply chain state, clears active workflow executions, and ensures test repeatability.",
        "difficulty": "Maintenance",
        "recommended_objective": "Reset and verify initial baseline metrics."
    }
]

@router.get("", response_model=List[Dict[str, Any]])
def list_scenarios():
    return AVAILABLE_SCENARIOS

@router.post("/{key}/trigger")
def trigger_scenario(key: str, db: Session = Depends(get_db)):
    """
    Applies real business environment state mutations corresponding to the scenario.
    """
    today = date.today()

    if key == "SUPPLIER_DELAY_APEX":
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-2026-8812").first()
        if po:
            po.status = "DELAYED"
            po.delay_days = 7
            po.revised_delivery_date = today + timedelta(days=8)

        # Mark incident as OPEN
        inc = db.query(OperationalIncident).filter(OperationalIncident.incident_key == "INC-2026-042").first()
        if inc:
            inc.status = "OPEN"
            inc.detected_at = datetime.utcnow()
        db.commit()

        return {
            "scenario": key,
            "status": "TRIGGERED",
            "message": "Inbound shipment PO-2026-8812 delayed by 7 days. Incident INC-2026-042 activated.",
            "recommended_objective": AVAILABLE_SCENARIOS[0]["recommended_objective"]
        }

    elif key == "DEMAND_SPIKE_CHICAGO":
        # Boost recent demand history in Chicago
        chicago_wh = db.query(Warehouse).filter(Warehouse.code == "WH-CHI").first()
        target_prod = db.query(Product).filter(Product.sku == "P-MOT-100").first()
        if chicago_wh and target_prod:
            recent_demands = db.query(DemandHistory).filter(
                DemandHistory.warehouse_id == chicago_wh.id,
                DemandHistory.product_id == target_prod.id
            ).order_by(DemandHistory.date.desc()).limit(5).all()
            for rd in recent_demands:
                rd.demand_qty = int(rd.demand_qty * 1.6)

        # Add urgent customer order
        urgent_order = CustomerOrder(
            order_number=f"ORD-SURGE-{today.strftime('%m%d')}",
            customer_name="Tesla Gigafactory Texas (Expedited Line)",
            order_date=today,
            required_delivery_date=today + timedelta(days=2),
            status="AT_RISK",
            priority="VIP",
            total_revenue=8500.0
        )
        db.add(urgent_order)
        db.flush()
        db.add(POLineItem(po_id=1, product_id=1, qty=25, unit_cost=185.0)) # dummy item or order line
        db.commit()

        return {
            "scenario": key,
            "status": "TRIGGERED",
            "message": "Demand increased by 60% for Servo Motors in Chicago. Urgent VIP order ORD-SURGE created.",
            "recommended_objective": AVAILABLE_SCENARIOS[1]["recommended_objective"]
        }

    elif key == "RESET_BASELINE":
        # Clean workflows, traces, and re-seed
        db.query(ActionExecution).delete()
        db.query(RecoveryPlan).delete()
        db.query(AgentTrace).delete()
        db.query(Workflow).delete()
        db.query(OperationalIncident).delete()
        db.query(DemandHistory).delete()
        db.query(POLineItem).delete()
        db.query(PurchaseOrder).delete()
        db.query(OrderLineItem).delete()
        db.query(CustomerOrder).delete()
        db.query(Inventory).delete()
        db.query(Product).delete()
        db.query(SupplierProduct).delete()
        db.query(Supplier).delete()
        db.query(Warehouse).delete()
        db.commit()

        seed_database(db)

        return {
            "scenario": key,
            "status": "RESET_COMPLETE",
            "message": "Environment successfully reset to pristine benchmark state."
        }

    raise HTTPException(status_code=400, detail=f"Scenario key '{key}' not supported.")
