import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.supply_chain import (
    Warehouse, Supplier, Product, ProductCategory, Inventory,
    DemandHistory, CustomerOrder, OrderLineItem
)
from app.services.inventory_service import InventoryService
from app.agents.impact_analysis import ImpactAnalysisAgent
from app.agents.state import OrbitWorkflowState

@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    # Seed minimal base entities
    wh = Warehouse(code="WH-CHI", name="Chicago Logistics Hub", location="Chicago, IL", capacity_units=150000)
    cat = ProductCategory(name="Industrial Automation", description="Motors and drives")
    db.add_all([wh, cat])
    db.flush()

    prod = Product(
        sku="P-MOT-100",
        name="High-Torque AC Servo Motor 750W",
        category_id=cat.id,
        unit_cost=185.0,
        selling_price=340.0,
        safety_stock=40,
        reorder_point=90
    )
    db.add(prod)
    db.flush()

    yield db
    db.close()

def test_available_inventory_and_allocation(memory_db):
    """Verifies that available inventory correctly accounts for reserved and allocated stock."""
    # When reserved == allocated (mirrored allocation model)
    avail1 = InventoryService.calculate_available_inventory(on_hand_qty=50, reserved_qty=15, allocated_qty=15)
    assert avail1 == 35

    # When reserved and allocated are distinct additive pools
    avail2 = InventoryService.calculate_available_inventory(on_hand_qty=50, reserved_qty=10, allocated_qty=15)
    assert avail2 == 25

    # When committed exceeds on-hand, floor at 0
    avail3 = InventoryService.calculate_available_inventory(on_hand_qty=20, reserved_qty=15, allocated_qty=15)
    assert avail3 == 5

    avail4 = InventoryService.calculate_available_inventory(on_hand_qty=10, reserved_qty=15, allocated_qty=10)
    assert avail4 == 0

def test_impact_analysis_normal_demand(memory_db):
    """Verifies impact analysis with standard empirical 30-day demand history."""
    wh = memory_db.query(Warehouse).first()
    prod = memory_db.query(Product).first()
    today = date.today()

    # Add inventory: 36 on hand, 12 reserved, 12 allocated -> 24 available
    inv = Inventory(
        warehouse_id=wh.id,
        product_id=prod.id,
        on_hand_qty=36,
        reserved_qty=12,
        allocated_qty=12
    )
    memory_db.add(inv)

    # 30 days of steady 12.0 units/day demand
    for i in range(30, 0, -1):
        dh = DemandHistory(
            warehouse_id=wh.id,
            product_id=prod.id,
            date=today - timedelta(days=i),
            demand_qty=12
        )
        memory_db.add(dh)

    # Add 2 customer orders within 7-day window
    co1 = CustomerOrder(
        order_number="ORD-TEST-1",
        customer_name="Boeing",
        order_date=today - timedelta(days=2),
        required_delivery_date=today + timedelta(days=3),
        status="AT_RISK",
        priority="VIP",
        total_revenue=3400.0
    )
    memory_db.add(co1)
    memory_db.flush()
    memory_db.add(OrderLineItem(order_id=co1.id, product_id=prod.id, warehouse_id=wh.id, ordered_qty=10, fulfilled_qty=0, unit_price=340.0))

    co2 = CustomerOrder(
        order_number="ORD-TEST-2",
        customer_name="Siemens",
        order_date=today - timedelta(days=1),
        required_delivery_date=today + timedelta(days=5),
        status="AT_RISK",
        priority="EXPEDITED",
        total_revenue=6800.0
    )
    memory_db.add(co2)
    memory_db.flush()
    memory_db.add(OrderLineItem(order_id=co2.id, product_id=prod.id, warehouse_id=wh.id, ordered_qty=20, fulfilled_qty=0, unit_price=340.0))
    memory_db.commit()

    # Execute Impact Analysis Agent
    state: OrbitWorkflowState = {
        "workflow_id": 1,
        "disruption_data": {
            "affected_product_id": prod.id,
            "affected_warehouse_id": wh.id,
            "delay_days": 7
        }
    }
    result = ImpactAnalysisAgent.execute(state, memory_db)
    impact = result["impact_data"]

    assert impact["on_hand_qty"] == 36
    assert impact["available_qty"] == 24
    assert impact["demand_history_records_count"] == 30
    assert impact["demand_history_status"] == "SUFFICIENT"
    assert impact["demand_spike_detected"] is False
    assert round(impact["daily_depletion_rate"], 1) == 12.0
    # Available runway: 24 / 12 = 2.0 days
    assert impact["runway_days"] == 2.0
    assert impact["total_at_risk_orders_count"] == 2
    assert impact["total_at_risk_units"] == 30
    # Shortfall: 30 demanded - 24 available = 6
    assert impact["shortfall_units"] == 6
    assert impact["revenue_at_risk"] == 10200.0
    assert impact["severity"] == "CRITICAL"

def test_impact_analysis_zero_demand(memory_db):
    """Verifies that zero demand history is handled gracefully with safe runway and no stockout."""
    wh = memory_db.query(Warehouse).first()
    prod = memory_db.query(Product).first()
    today = date.today()

    inv = Inventory(
        warehouse_id=wh.id,
        product_id=prod.id,
        on_hand_qty=20,
        reserved_qty=5,
        allocated_qty=5
    )
    memory_db.add(inv)

    # 15 days of 0 demand
    for i in range(15, 0, -1):
        memory_db.add(DemandHistory(
            warehouse_id=wh.id,
            product_id=prod.id,
            date=today - timedelta(days=i),
            demand_qty=0
        ))
    memory_db.commit()

    state: OrbitWorkflowState = {
        "workflow_id": 2,
        "disruption_data": {
            "affected_product_id": prod.id,
            "affected_warehouse_id": wh.id,
            "delay_days": 7
        }
    }
    result = ImpactAnalysisAgent.execute(state, memory_db)
    impact = result["impact_data"]

    assert impact["daily_depletion_rate"] == 0.0
    assert impact["runway_days"] == 999.0
    assert impact["stockout_before_replenishment"] is False
    assert "No projected stockout" in impact["stockout_projected_date"]

def test_impact_analysis_missing_history(memory_db):
    """Verifies explicit handling and honest reporting when demand history is completely missing."""
    wh = memory_db.query(Warehouse).first()
    prod = memory_db.query(Product).first()

    inv = Inventory(
        warehouse_id=wh.id,
        product_id=prod.id,
        on_hand_qty=25,
        reserved_qty=5,
        allocated_qty=5
    )
    memory_db.add(inv)
    memory_db.commit()

    state: OrbitWorkflowState = {
        "workflow_id": 3,
        "disruption_data": {
            "affected_product_id": prod.id,
            "affected_warehouse_id": wh.id,
            "delay_days": 7
        }
    }
    result = ImpactAnalysisAgent.execute(state, memory_db)
    impact = result["impact_data"]

    assert impact["demand_history_records_count"] == 0
    assert impact["demand_history_status"] == "NO_HISTORY"
    assert "HEURISTIC_FALLBACK" in impact["velocity_source"]
    assert impact["daily_depletion_rate"] > 0
    assert impact["runway_days"] > 0

def test_impact_analysis_demand_spike(memory_db):
    """Verifies that an unusual demand spike in the recent 7 days is detected and accelerates depletion rate."""
    wh = memory_db.query(Warehouse).first()
    prod = memory_db.query(Product).first()
    today = date.today()

    inv = Inventory(
        warehouse_id=wh.id,
        product_id=prod.id,
        on_hand_qty=100,
        reserved_qty=10,
        allocated_qty=10
    )
    memory_db.add(inv)

    # First 21 days: normal demand of 8 units/day
    for i in range(28, 7, -1):
        memory_db.add(DemandHistory(
            warehouse_id=wh.id,
            product_id=prod.id,
            date=today - timedelta(days=i),
            demand_qty=8
        ))
    # Last 7 days: demand surge to 25 units/day (spike factor > 3x)
    for i in range(7, 0, -1):
        memory_db.add(DemandHistory(
            warehouse_id=wh.id,
            product_id=prod.id,
            date=today - timedelta(days=i),
            demand_qty=25
        ))
    memory_db.commit()

    state: OrbitWorkflowState = {
        "workflow_id": 4,
        "disruption_data": {
            "affected_product_id": prod.id,
            "affected_warehouse_id": wh.id,
            "delay_days": 7
        }
    }
    result = ImpactAnalysisAgent.execute(state, memory_db)
    impact = result["impact_data"]

    assert impact["demand_spike_detected"] is True
    assert impact["velocity_source"] == "EMPIRICAL_DEMAND_SPIKE_ACCELERATED"
    # Velocity should reflect the recent spike rate (>= 25) rather than the slower 30-day baseline (~12)
    assert impact["daily_depletion_rate"] >= 24.0
    # Available runway for 90 units at 25/day is 3.6 days, accelerating stockout
    assert impact["runway_days"] <= 4.0
