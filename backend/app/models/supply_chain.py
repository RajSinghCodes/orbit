from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)  # e.g., "Chicago, IL"
    capacity_units = Column(Integer, nullable=False)
    current_utilization = Column(Float, default=0.0)  # Percentage 0-100
    operating_cost_per_day = Column(Float, default=500.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventories = relationship("Inventory", back_populates="warehouse", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="warehouse")
    order_items = relationship("OrderLineItem", back_populates="warehouse")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    tier = Column(String(20), default="Tier 1")  # Tier 1, Tier 2, etc.
    reliability_score = Column(Float, default=0.95)  # Historical OTIF (0.0 - 1.0)
    avg_lead_time_days = Column(Integer, default=7)
    on_time_delivery_rate = Column(Float, default=0.92)
    quality_rating = Column(Float, default=4.8)  # 1.0 - 5.0
    contact_email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("SupplierProduct", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    incidents = relationship("OperationalIncident", back_populates="supplier")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    unit_cost = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    holding_cost_per_day = Column(Float, default=0.05)
    safety_stock = Column(Integer, default=50)
    reorder_point = Column(Integer, default=100)
    min_order_qty = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("ProductCategory", back_populates="products")
    supplier_options = relationship("SupplierProduct", back_populates="product")
    inventories = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderLineItem", back_populates="product")
    po_items = relationship("POLineItem", back_populates="product")
    demand_records = relationship("DemandHistory", back_populates="product")


class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    unit_cost = Column(Float, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    min_order_qty = Column(Integer, default=50)
    max_capacity_per_week = Column(Integer, default=500)
    is_primary = Column(Boolean, default=False)

    supplier = relationship("Supplier", back_populates="products")
    product = relationship("Product", back_populates="supplier_options")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    on_hand_qty = Column(Integer, default=0, nullable=False)
    reserved_qty = Column(Integer, default=0, nullable=False)
    allocated_qty = Column(Integer, default=0, nullable=False)
    in_transit_qty = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="inventories")
    product = relationship("Product", back_populates="inventories")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(50), nullable=False)  # TRANSFER, RECEIPT, FULFILLMENT, ADJUSTMENT
    reference_id = Column(String(100), nullable=True)  # PO or Order or Transfer ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    qty = Column(Integer, nullable=False)
    movement_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="COMPLETED")  # PENDING, IN_TRANSIT, COMPLETED, CANCELLED


class CustomerOrder(Base):
    __tablename__ = "customer_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)
    order_date = Column(Date, default=date.today)
    required_delivery_date = Column(Date, nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, AT_RISK, FULFILLED, DELAYED, CANCELLED
    priority = Column(String(20), default="STANDARD")  # STANDARD, EXPEDITED, VIP
    total_revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    line_items = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")


class OrderLineItem(Base):
    __tablename__ = "order_line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("customer_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    ordered_qty = Column(Integer, nullable=False)
    fulfilled_qty = Column(Integer, default=0)
    unit_price = Column(Float, nullable=False)

    order = relationship("CustomerOrder", back_populates="line_items")
    product = relationship("Product", back_populates="order_items")
    warehouse = relationship("Warehouse", back_populates="order_items")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    order_date = Column(Date, default=date.today)
    expected_delivery_date = Column(Date, nullable=False)
    revised_delivery_date = Column(Date, nullable=True)
    delay_days = Column(Integer, default=0)
    status = Column(String(50), default="CONFIRMED")  # CONFIRMED, DELAYED, IN_TRANSIT, RECEIVED, CANCELLED
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    warehouse = relationship("Warehouse", back_populates="purchase_orders")
    line_items = relationship("POLineItem", back_populates="purchase_order", cascade="all, delete-orphan")


class POLineItem(Base):
    __tablename__ = "po_line_items"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    product = relationship("Product", back_populates="po_items")


class DemandHistory(Base):
    __tablename__ = "demand_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    demand_qty = Column(Integer, nullable=False)

    product = relationship("Product", back_populates="demand_records")


class OperationalIncident(Base):
    __tablename__ = "operational_incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_key = Column(String(50), unique=True, nullable=False, index=True)
    incident_type = Column(String(50), nullable=False)  # SUPPLIER_DELAY, DEMAND_SPIKE, STOCKOUT, PRICE_SURGE
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN")  # OPEN, INVESTIGATING, MITIGATING, RESOLVED
    affected_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    affected_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    details_json = Column(JSON, default=dict)

    supplier = relationship("Supplier", back_populates="incidents")
