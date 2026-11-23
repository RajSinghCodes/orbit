from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Warehouse Schemas
class WarehouseBase(BaseModel):
    code: str
    name: str
    location: str
    capacity_units: int
    current_utilization: float = 0.0
    operating_cost_per_day: float = 500.0

class WarehouseOut(WarehouseBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Supplier Schemas
class SupplierBase(BaseModel):
    code: str
    name: str
    tier: str = "Tier 1"
    reliability_score: float = 0.95
    avg_lead_time_days: int = 7
    on_time_delivery_rate: float = 0.92
    quality_rating: float = 4.8
    contact_email: Optional[str] = None

class SupplierOut(SupplierBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    category_id: Optional[int] = None
    unit_cost: float
    selling_price: float
    holding_cost_per_day: float = 0.05
    safety_stock: int = 50
    reorder_point: int = 100
    min_order_qty: int = 20

class ProductOut(ProductBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Inventory Schemas
class InventoryBase(BaseModel):
    warehouse_id: int
    product_id: int
    on_hand_qty: int
    reserved_qty: int = 0
    allocated_qty: int = 0
    in_transit_qty: int = 0

class InventoryDetail(InventoryBase):
    id: int
    warehouse_name: str
    warehouse_code: str
    product_sku: str
    product_name: str
    available_qty: int
    unit_cost: float
    total_value: float
    safety_stock: int
    runway_days: float
    stockout_risk: str  # SAFE, WARNING, CRITICAL

    class Config:
        from_attributes = True

# Customer Order Schemas
class OrderLineItemOut(BaseModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    ordered_qty: int
    fulfilled_qty: int
    unit_price: float

    class Config:
        from_attributes = True

class CustomerOrderOut(BaseModel):
    id: int
    order_number: str
    customer_name: str
    order_date: date
    required_delivery_date: date
    status: str
    priority: str
    total_revenue: float
    line_items: List[OrderLineItemOut] = []

    class Config:
        from_attributes = True

# Purchase Order Schemas
class POLineItemOut(BaseModel):
    id: int
    product_id: int
    product_sku: str
    product_name: str
    qty: int
    unit_cost: float

    class Config:
        from_attributes = True

class PurchaseOrderOut(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    supplier_name: str
    warehouse_id: int
    warehouse_name: str
    order_date: date
    expected_delivery_date: date
    revised_delivery_date: Optional[date] = None
    delay_days: int = 0
    status: str
    total_cost: float
    line_items: List[POLineItemOut] = []

    class Config:
        from_attributes = True

# Operational Incident Schemas
class OperationalIncidentOut(BaseModel):
    id: int
    incident_key: str
    incident_type: str
    title: str
    description: str
    severity: str
    status: str
    affected_supplier_id: Optional[int] = None
    affected_supplier_name: Optional[str] = None
    affected_warehouse_id: Optional[int] = None
    affected_warehouse_name: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    details_json: Dict[str, Any] = {}

    class Config:
        from_attributes = True

# Dashboard Overview Schema
class DashboardOverview(BaseModel):
    total_inventory_value: float
    total_warehouses: int
    total_suppliers: int
    total_products: int
    active_disruptions: int
    products_at_risk: int
    orders_at_risk_count: int
    revenue_at_risk: float
    avg_supplier_reliability: float
    pending_approvals: int
    recent_incidents: List[OperationalIncidentOut] = []
