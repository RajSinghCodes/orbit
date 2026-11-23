from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.supply_chain import (
    Warehouse, Supplier, Product, Inventory, CustomerOrder,
    PurchaseOrder, DemandHistory
)
from app.schemas.supply_chain import (
    WarehouseOut, SupplierOut, ProductOut, InventoryDetail,
    CustomerOrderOut, PurchaseOrderOut
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/supply-chain", tags=["Supply Chain Intelligence"])

@router.get("/warehouses", response_model=List[WarehouseOut])
def get_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

@router.get("/suppliers", response_model=List[SupplierOut])
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()

@router.get("/products", response_model=List[ProductOut])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.get("/inventory", response_model=List[InventoryDetail])
def get_inventory(
    warehouse_id: Optional[int] = Query(None, description="Optional filter by warehouse"),
    db: Session = Depends(get_db)
):
    """Retrieves full inventory ledger with deterministic runway and risk status."""
    return InventoryService.get_inventory_status(db, warehouse_id=warehouse_id)

@router.get("/customer-orders", response_model=List[CustomerOrderOut])
def get_customer_orders(
    status: Optional[str] = Query(None, description="Filter by status e.g. AT_RISK"),
    db: Session = Depends(get_db)
):
    query = db.query(CustomerOrder)
    if status:
        query = query.filter(CustomerOrder.status == status)
    orders = query.order_by(CustomerOrder.required_delivery_date.asc()).all()

    # Enrich line item names
    enriched = []
    for o in orders:
        items = []
        for it in o.line_items:
            items.append({
                "id": it.id,
                "product_id": it.product_id,
                "product_sku": it.product.sku if it.product else "UNKNOWN",
                "product_name": it.product.name if it.product else "Unknown Product",
                "warehouse_id": it.warehouse_id,
                "warehouse_name": it.warehouse.name if it.warehouse else "Unknown Facility",
                "ordered_qty": it.ordered_qty,
                "fulfilled_qty": it.fulfilled_qty,
                "unit_price": it.unit_price
            })
        enriched.append({
            "id": o.id,
            "order_number": o.order_number,
            "customer_name": o.customer_name,
            "order_date": o.order_date,
            "required_delivery_date": o.required_delivery_date,
            "status": o.status,
            "priority": o.priority,
            "total_revenue": o.total_revenue,
            "line_items": items
        })
    return enriched

@router.get("/purchase-orders", response_model=List[PurchaseOrderOut])
def get_purchase_orders(db: Session = Depends(get_db)):
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.expected_delivery_date.asc()).all()
    enriched = []
    for po in pos:
        items = []
        for it in po.line_items:
            items.append({
                "id": it.id,
                "product_id": it.product_id,
                "product_sku": it.product.sku if it.product else "UNKNOWN",
                "product_name": it.product.name if it.product else "Unknown Product",
                "qty": it.qty,
                "unit_cost": it.unit_cost
            })
        enriched.append({
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "supplier_name": po.supplier.name if po.supplier else "Unknown Supplier",
            "warehouse_id": po.warehouse_id,
            "warehouse_name": po.warehouse.name if po.warehouse else "Unknown Facility",
            "order_date": po.order_date,
            "expected_delivery_date": po.expected_delivery_date,
            "revised_delivery_date": po.revised_delivery_date,
            "delay_days": po.delay_days,
            "status": po.status,
            "total_cost": po.total_cost,
            "line_items": items
        })
    return enriched

@router.get("/demand-history")
def get_demand_history(
    product_id: Optional[int] = Query(1, description="Product ID"),
    warehouse_id: Optional[int] = Query(1, description="Warehouse ID"),
    db: Session = Depends(get_db)
):
    records = db.query(DemandHistory).filter(
        DemandHistory.product_id == product_id,
        DemandHistory.warehouse_id == warehouse_id
    ).order_by(DemandHistory.date.asc()).all()

    return [
        {"date": str(r.date), "demand_qty": r.demand_qty}
        for r in records
    ]
