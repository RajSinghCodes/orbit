import pytest
from app.services.inventory_service import InventoryService
from app.services.forecasting_service import ForecastingService
from app.services.supplier_service import SupplierService

def test_inventory_runway_calculation():
    # 120 units on hand, 12 units/day velocity -> 10.0 days runway
    runway = InventoryService.calculate_runway_days(on_hand_qty=120, daily_demand=12.0)
    assert runway == 10.0

    # Zero velocity returns safe fallback
    zero_runway = InventoryService.calculate_runway_days(on_hand_qty=50, daily_demand=0.0)
    assert zero_runway == 999.0

def test_stockout_risk_classification():
    # 18 units with safety stock 40 and runway 1.5 days -> CRITICAL
    risk_crit = InventoryService.calculate_stockout_risk(on_hand_qty=18, safety_stock=40, runway_days=1.5)
    assert risk_crit == "CRITICAL"

    # 35 units with safety stock 40 and runway 6.0 days -> WARNING
    risk_warn = InventoryService.calculate_stockout_risk(on_hand_qty=35, safety_stock=40, runway_days=6.0)
    assert risk_warn == "WARNING"

    # 100 units with safety stock 40 and runway 14.0 days -> SAFE
    risk_safe = InventoryService.calculate_stockout_risk(on_hand_qty=100, safety_stock=40, runway_days=14.0)
    assert risk_safe == "SAFE"

def test_forecasting_metrics():
    actuals = [10.0, 12.0, 15.0, 14.0, 16.0]
    preds = [10.0, 11.0, 14.0, 15.0, 15.0]

    metrics = ForecastingService.calculate_metrics(actuals, preds)
    assert metrics["mae"] == 0.8
    assert metrics["rmse"] > 0
    assert metrics["mape"] > 0

def test_supplier_scoring():
    # Supplier with 98% reliability, 3-day lead time vs 86% reliability, 12-day lead time
    fast_score = SupplierService.calculate_supplier_score(
        reliability=0.98,
        lead_time_days=3,
        unit_price=205.0,
        max_lead_time=14,
        max_unit_price=250.0
    )

    slow_score = SupplierService.calculate_supplier_score(
        reliability=0.86,
        lead_time_days=12,
        unit_price=175.0,
        max_lead_time=14,
        max_unit_price=250.0
    )

    assert fast_score > slow_score
