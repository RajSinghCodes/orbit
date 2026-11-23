from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supply_chain import (
    OperationalIncident, Supplier, Warehouse, Product, Inventory,
    PurchaseOrder, POLineItem
)
from app.schemas.supply_chain import OperationalIncidentOut
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/incidents", tags=["Operational Incidents"])

def _enrich_incident_details(inc: OperationalIncident, db: Session) -> dict:
    details = dict(inc.details_json or {})
    wh_id = inc.affected_warehouse_id

    # Try to resolve product
    prod = None
    if "product_sku" in details:
        prod = db.query(Product).filter(Product.sku == details["product_sku"]).first()
    elif "po_number" in details:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == details["po_number"]).first()
        if po and po.line_items:
            prod = po.line_items[0].product
            details["product_sku"] = prod.sku

    if prod and wh_id:
        delay_days = details.get("delay_days", 7)
        # Fetch current inventory
        inv = db.query(Inventory).filter(
            Inventory.warehouse_id == wh_id,
            Inventory.product_id == prod.id
        ).first()

        on_hand = inv.on_hand_qty if inv else 0
        reserved = inv.reserved_qty if inv else 0
        allocated = inv.allocated_qty if inv else 0
        available = InventoryService.calculate_available_inventory(on_hand, reserved, allocated)

        # Historical demand
        demand_stats = InventoryService.calculate_historical_daily_demand(
            db=db,
            product_id=prod.id,
            warehouse_id=wh_id,
            lookback_days=30
        )
        daily_velocity = demand_stats["avg_daily_demand"] if demand_stats["avg_daily_demand"] > 0 else 12.0
        velocity_source = "30-day demand history" if demand_stats["status"] != "NO_HISTORY" else "Fallback Model"

        # Coverage
        coverage = InventoryService.calculate_inventory_coverage(on_hand, available, daily_velocity)

        # At risk orders
        at_risk_orders = InventoryService.identify_at_risk_orders(
            db=db,
            product_id=prod.id,
            warehouse_id=wh_id,
            disruption_days=delay_days
        )
        revenue_at_risk = round(sum([o["order_revenue"] for o in at_risk_orders]), 2)
        quantity_at_risk = sum([o["ordered_qty"] for o in at_risk_orders])

        details.update({
            "product_id": prod.id,
            "product_sku": prod.sku,
            "product_name": prod.name,
            "on_hand_qty": on_hand,
            "reserved_qty": reserved,
            "allocated_qty": allocated,
            "available_qty": available,
            "safety_stock": prod.safety_stock,
            "daily_velocity": daily_velocity,
            "velocity_source": velocity_source,
            "demand_history_records_count": demand_stats["record_count"],
            "runway_days": coverage["available_runway_days"],
            "gross_runway_days": coverage["gross_runway_days"],
            "stockout_date": coverage["stockout_date_str"],
            "orders_at_risk_count": len(at_risk_orders),
            "quantity_at_risk": quantity_at_risk,
            "revenue_at_risk": revenue_at_risk,
            "at_risk_orders": at_risk_orders
        })

    return details

@router.get("", response_model=List[OperationalIncidentOut])
def get_incidents(db: Session = Depends(get_db)):
    incidents = db.query(OperationalIncident).order_by(OperationalIncident.detected_at.desc()).all()
    results = []
    for inc in incidents:
        sup = db.query(Supplier).filter(Supplier.id == inc.affected_supplier_id).first() if inc.affected_supplier_id else None
        wh = db.query(Warehouse).filter(Warehouse.id == inc.affected_warehouse_id).first() if inc.affected_warehouse_id else None
        enriched_details = _enrich_incident_details(inc, db)
        results.append({
            "id": inc.id,
            "incident_key": inc.incident_key,
            "incident_type": inc.incident_type,
            "title": inc.title,
            "description": inc.description,
            "severity": inc.severity,
            "status": inc.status,
            "affected_supplier_id": inc.affected_supplier_id,
            "affected_supplier_name": sup.name if sup else None,
            "affected_warehouse_id": inc.affected_warehouse_id,
            "affected_warehouse_name": wh.name if wh else None,
            "detected_at": inc.detected_at,
            "resolved_at": inc.resolved_at,
            "details_json": enriched_details
        })
    return results

@router.get("/{id}", response_model=OperationalIncidentOut)
def get_incident(id: int, db: Session = Depends(get_db)):
    inc = db.query(OperationalIncident).filter(OperationalIncident.id == id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    sup = db.query(Supplier).filter(Supplier.id == inc.affected_supplier_id).first() if inc.affected_supplier_id else None
    wh = db.query(Warehouse).filter(Warehouse.id == inc.affected_warehouse_id).first() if inc.affected_warehouse_id else None
    enriched_details = _enrich_incident_details(inc, db)
    return {
        "id": inc.id,
        "incident_key": inc.incident_key,
        "incident_type": inc.incident_type,
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "affected_supplier_id": inc.affected_supplier_id,
        "affected_supplier_name": sup.name if sup else None,
        "affected_warehouse_id": inc.affected_warehouse_id,
        "affected_warehouse_name": wh.name if wh else None,
        "detected_at": inc.detected_at,
        "resolved_at": inc.resolved_at,
        "details_json": enriched_details
    }
