import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.data.seed_data import seed_database
from app.services.optimization_service import OptimizationService

@pytest.fixture
def seeded_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    seed_database(db)
    yield db
    db.close()

def test_ortools_split_allocation_optimization():
    """Verifies that Google OR-Tools solves for the cost-optimal allocation respecting surplus and capacity."""
    surplus_warehouses = [
        {"warehouse_id": 2, "warehouse_name": "Dallas Hub", "transferable_qty": 40, "freight_cost_per_unit": 4.50, "transfer_lead_time_days": 2}
    ]
    alt_suppliers = [
        {"supplier_id": 2, "supplier_name": "Nexus Precision", "unit_cost": 205.0, "lead_time_days": 3, "min_order_qty": 20, "max_capacity_per_week": 250}
    ]

    shortfall = 50
    # Solve with OR-Tools
    result = OptimizationService.solve_optimal_split_allocation(
        shortfall_qty=shortfall,
        surplus_warehouses=surplus_warehouses,
        alt_suppliers=alt_suppliers,
        max_transfer_ratio=0.50
    )

    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    assert result["total_allocated"] >= shortfall
    # With max_transfer_ratio 0.50, transfer should be bounded to min(40, 25) = 25 units
    transfers = result["transfers"]
    assert len(transfers) == 1
    assert transfers[0]["allocated_qty"] == 25
    assert transfers[0]["transfer_cost"] == 25 * 4.50

    # Remaining 25 units fulfilled by purchase order
    pos = result["purchase_orders"]
    assert len(pos) == 1
    assert pos[0]["allocated_qty"] == 25
    assert pos[0]["purchase_cost"] == 25 * 205.0

def test_deterministic_recovery_timeline_simulation():
    """Verifies chronological simulation produces exact integer metrics without fabricated probabilities."""
    today = date.today()
    at_risk_orders = [
        {"order_id": 101, "customer_name": "Cust A", "priority": "VIP", "required_delivery_date": str(today + timedelta(days=2)), "ordered_qty": 10, "order_revenue": 3400.0},
        {"order_id": 102, "customer_name": "Cust B", "priority": "EXPEDITED", "required_delivery_date": str(today + timedelta(days=4)), "ordered_qty": 15, "order_revenue": 5100.0},
        {"order_id": 103, "customer_name": "Cust C", "priority": "STANDARD", "required_delivery_date": str(today + timedelta(days=6)), "ordered_qty": 20, "order_revenue": 6800.0},
    ]

    # Scenario A: Initial stock is 6 units, 30 units arrive on Day 3
    # On Day 2: Cust A needs 10 units -> stock 6 covers 6, 4 units delayed!
    # On Day 3: 30 units arrive -> stock = 30.
    # On Day 4: Cust B needs 15 units -> fulfilled on time! stock = 15.
    # On Day 6: Cust C needs 20 units -> stock 15 covers 15, 5 units delayed!
    sim_a = OptimizationService.simulate_recovery_schedule(
        available_qty=6,
        safety_stock_released=0,
        replenishments=[{"arrival_day": 3, "qty": 30}],
        at_risk_orders=at_risk_orders,
        reference_date=today
    )

    assert sim_a["orders_protected"] == 1  # Only Cust B fulfilled 100% on time
    assert sim_a["orders_delayed"] == 2    # Cust A and Cust C delayed
    assert sim_a["orders_protected_revenue"] == 5100.0
    assert sim_a["stockout_units"] == 9    # 4 (Cust A) + 5 (Cust C)
    assert sim_a["service_level"] == round(1 / 3, 3)
    assert sim_a["stockout_risk_score"] == round(9 / 45, 3)

    # Scenario B: Transfer of 15 units arrives on Day 2, and PO of 30 units arrives on Day 3
    # Stock on Day 2: 6 + 15 = 21 -> Cust A (10) fulfilled on time! Stock = 11.
    # Stock on Day 3: 11 + 30 = 41.
    # Day 4: Cust B (15) fulfilled on time! Stock = 26.
    # Day 6: Cust C (20) fulfilled on time! Stock = 6.
    sim_b = OptimizationService.simulate_recovery_schedule(
        available_qty=6,
        safety_stock_released=0,
        replenishments=[{"arrival_day": 2, "qty": 15}, {"arrival_day": 3, "qty": 30}],
        at_risk_orders=at_risk_orders,
        reference_date=today
    )

    assert sim_b["orders_protected"] == 3  # 100% protected
    assert sim_b["orders_delayed"] == 0
    assert sim_b["stockout_units"] == 0
    assert sim_b["service_level"] == 1.0
    assert sim_b["stockout_risk_score"] == 0.0
    assert sim_b["orders_protected_revenue"] == 15300.0

def test_formulate_recovery_strategies_and_rejection(seeded_db):
    """Verifies strategy formulation on real seeded database and explicit rejection of infeasible options."""
    # Disrupted supplier 1 (Apex), Product 1 (P-MOT-100), Warehouse 1 (Chicago)
    strategies = OptimizationService.formulate_recovery_strategies(
        db=seeded_db,
        disrupted_supplier_id=1,
        affected_product_id=1,
        affected_warehouse_id=1,
        shortfall_qty=50,
        disruption_days=7
    )

    assert len(strategies) == 3

    # Strategy 2 (Balanced Transfer & Purchase) is recommended
    strat2 = [s for s in strategies if s["strategy_type"] == "BALANCED_TRANSFER_PURCHASE"][0]
    assert strat2["is_recommended"] is True
    assert strat2["is_feasible"] is True
    assert strat2["orders_protected"] > 0
    assert strat2["total_recovery_cost"] > 0
    assert len(strat2["actions"]) >= 2  # Inter-warehouse transfer + PO

    # Strategy 1 (Expedited PO)
    strat1 = [s for s in strategies if s["strategy_type"] == "EXPEDITED_ALTERNATIVE"][0]
    assert strat1["is_feasible"] is True
    assert strat1["is_recommended"] is False
    assert strat1["total_recovery_cost"] > strat2["total_recovery_cost"]  # Expedited air freight premium

    # Test rejection behavior with an impossible shortfall exceeding supplier capacity
    absurd_shortfall = 50000  # Exceeds supplier capacity of 250 units/week
    absurd_strategies = OptimizationService.formulate_recovery_strategies(
        db=seeded_db,
        disrupted_supplier_id=1,
        affected_product_id=1,
        affected_warehouse_id=1,
        shortfall_qty=absurd_shortfall,
        disruption_days=7
    )

    strat1_rejected = [s for s in absurd_strategies if s["strategy_type"] == "EXPEDITED_ALTERNATIVE"][0]
    assert strat1_rejected["is_feasible"] is False
    assert "exceeds" in strat1_rejected["rejection_reason"].lower()
    assert strat1_rejected["orders_protected"] == 0
    assert strat1_rejected["service_level"] == 0.0
