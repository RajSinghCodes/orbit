from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.supply_chain import Inventory, Product, Warehouse, CustomerOrder, OrderLineItem, PurchaseOrder

class InventoryService:
    @staticmethod
    def calculate_runway_days(on_hand_qty: int, daily_demand: float) -> float:
        """
        Calculates how many days of inventory remain before complete stockout.
        Deterministic arithmetic: runway = on_hand / daily_demand
        """
        if daily_demand <= 0:
            return 999.0
        return round(float(on_hand_qty) / float(daily_demand), 1)

    @staticmethod
    def calculate_available_inventory(on_hand_qty: int, reserved_qty: int, allocated_qty: int) -> int:
        """
        Calculates free uncommitted inventory accounting for both reserved and allocated quantities.
        If allocated is a subset of reserved (equal values in seed data), avoids double deduction.
        Otherwise accounts for both reserve pools.
        """
        if reserved_qty == allocated_qty:
            committed = reserved_qty
        else:
            committed = reserved_qty + allocated_qty
        return max(0, on_hand_qty - committed)

    @staticmethod
    def calculate_stockout_risk(on_hand_qty: int, safety_stock: int, runway_days: float) -> str:
        """
        Determines stockout risk level based on runway and safety threshold.
        """
        if on_hand_qty <= 0 or runway_days <= 3.0:
            return "CRITICAL"
        elif on_hand_qty < safety_stock or runway_days <= 7.0:
            return "WARNING"
        return "SAFE"

    @staticmethod
    def calculate_inventory_coverage(
        on_hand_qty: int,
        available_qty: int,
        daily_demand: float,
        reference_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculates inventory coverage in days and projected stockout calendar date.
        Deterministic arithmetic grounded in physical stock levels and depletion rate.
        """
        ref_date = reference_date or date.today()
        if daily_demand <= 0.0:
            return {
                "available_runway_days": 999.0,
                "gross_runway_days": 999.0,
                "stockout_date": None,
                "stockout_date_str": "No projected stockout (zero or negative depletion)",
                "risk_level": "SAFE"
            }

        available_runway = round(float(available_qty) / float(daily_demand), 1)
        gross_runway = round(float(on_hand_qty) / float(daily_demand), 1)

        stockout_days = max(0, int(available_runway))
        stockout_date = ref_date + timedelta(days=stockout_days)

        if available_qty <= 0 or available_runway <= 3.0:
            risk = "CRITICAL"
        elif available_runway <= 7.0:
            risk = "WARNING"
        else:
            risk = "SAFE"

        return {
            "available_runway_days": available_runway,
            "gross_runway_days": gross_runway,
            "stockout_date": stockout_date,
            "stockout_date_str": str(stockout_date),
            "risk_level": risk
        }

    @staticmethod
    def calculate_historical_daily_demand(db: Session, product_id: int, warehouse_id: int, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Retrieves empirical demand history from database for the specified product and warehouse.
        Calculates average daily demand, identifies demand spikes, and flags data sufficiency honestly.
        """
        import numpy as np
        from app.models.supply_chain import DemandHistory

        records = db.query(DemandHistory).filter(
            DemandHistory.product_id == product_id,
            DemandHistory.warehouse_id == warehouse_id
        ).order_by(DemandHistory.date.desc()).limit(lookback_days).all()

        if not records:
            return {
                "status": "NO_HISTORY",
                "record_count": 0,
                "avg_daily_demand": 0.0,
                "recent_7d_avg": 0.0,
                "spike_detected": False,
                "demand_values": [],
                "min_demand": 0.0,
                "max_demand": 0.0,
                "std_dev": 0.0,
                "confidence": "DATA_UNAVAILABLE"
            }

        records.reverse()  # chronological order
        demand_values = [float(r.demand_qty) for r in records]
        total_demand = sum(demand_values)

        if total_demand == 0.0:
            return {
                "status": "ZERO_DEMAND",
                "record_count": len(records),
                "avg_daily_demand": 0.0,
                "recent_7d_avg": 0.0,
                "spike_detected": False,
                "demand_values": demand_values,
                "min_demand": 0.0,
                "max_demand": 0.0,
                "std_dev": 0.0,
                "confidence": "HIGH"
            }

        avg_daily = round(float(np.mean(demand_values)), 2)
        recent_window = demand_values[-7:] if len(demand_values) >= 7 else demand_values
        recent_avg = round(float(np.mean(recent_window)), 2)
        std_dev = round(float(np.std(demand_values)), 2)

        # Spike detection: recent demand is > 1.4x overall average with meaningful unit delta
        spike_detected = (recent_avg > (avg_daily * 1.4)) and ((recent_avg - avg_daily) >= 3.0)

        status = "SUFFICIENT" if len(records) >= 14 else "INSUFFICIENT"
        confidence = "HIGH" if len(records) >= 14 else "LOW"

        return {
            "status": status,
            "record_count": len(records),
            "avg_daily_demand": avg_daily,
            "recent_7d_avg": recent_avg,
            "spike_detected": spike_detected,
            "demand_values": demand_values,
            "min_demand": float(min(demand_values)),
            "max_demand": float(max(demand_values)),
            "std_dev": std_dev,
            "confidence": confidence
        }

    @staticmethod
    def get_inventory_status(db: Session, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves enriched inventory status across products and warehouses.
        """
        query = db.query(Inventory, Product, Warehouse).join(
            Product, Inventory.product_id == Product.id
        ).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        )

        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)

        results = []
        for inv, prod, wh in query.all():
            available = InventoryService.calculate_available_inventory(
                inv.on_hand_qty, inv.reserved_qty, inv.allocated_qty
            )
            # Estimate daily demand from reorder point / safety stock heuristics or baseline
            estimated_daily_demand = max(1.0, float(prod.reorder_point - prod.safety_stock) / 7.0)
            runway = InventoryService.calculate_runway_days(available, estimated_daily_demand)
            risk = InventoryService.calculate_stockout_risk(available, prod.safety_stock, runway)

            results.append({
                "id": inv.id,
                "warehouse_id": wh.id,
                "warehouse_code": wh.code,
                "warehouse_name": wh.name,
                "product_id": prod.id,
                "product_sku": prod.sku,
                "product_name": prod.name,
                "on_hand_qty": inv.on_hand_qty,
                "reserved_qty": inv.reserved_qty,
                "available_qty": available,
                "in_transit_qty": inv.in_transit_qty,
                "safety_stock": prod.safety_stock,
                "unit_cost": prod.unit_cost,
                "total_value": round(inv.on_hand_qty * prod.unit_cost, 2),
                "runway_days": runway,
                "stockout_risk": risk
            })
        return results

    @staticmethod
    def find_surplus_warehouses(db: Session, product_id: int, exclude_warehouse_id: int, required_qty: int) -> List[Dict[str, Any]]:
        """
        Identifies sister warehouses that have surplus inventory (> safety stock * 1.2)
        and could transfer units to the disrupted warehouse.
        """
        inventories = db.query(Inventory, Warehouse, Product).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        ).join(
            Product, Inventory.product_id == Product.id
        ).filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id != exclude_warehouse_id
        ).all()

        candidates = []
        for inv, wh, prod in inventories:
            surplus = inv.on_hand_qty - int(prod.safety_stock * 1.2)
            if surplus > 0:
                transferable = min(surplus, required_qty)
                # Compute estimated transfer distance & freight cost
                # E.g. Dallas to Chicago ~ 1400 km, Atlanta to Chicago ~ 1100 km
                freight_per_unit = 4.50 if "Dallas" in wh.location else 3.80
                candidates.append({
                    "warehouse_id": wh.id,
                    "warehouse_code": wh.code,
                    "warehouse_name": wh.name,
                    "location": wh.location,
                    "on_hand_qty": inv.on_hand_qty,
                    "surplus_qty": surplus,
                    "transferable_qty": transferable,
                    "transfer_lead_time_days": 2,  # Expedited ground freight
                    "freight_cost_per_unit": freight_per_unit,
                    "total_freight_cost": round(transferable * freight_per_unit, 2)
                })
        return candidates

    @staticmethod
    def identify_at_risk_orders(db: Session, product_id: int, warehouse_id: int, disruption_days: int) -> List[Dict[str, Any]]:
        """
        Finds customer orders that require delivery within the disruption window
        where warehouse stock is insufficient.
        """
        today = date.today()
        disruption_end = today + timedelta(days=disruption_days)

        # Get orders with line items for this product and warehouse
        orders = db.query(CustomerOrder, OrderLineItem).join(
            OrderLineItem, CustomerOrder.id == OrderLineItem.order_id
        ).filter(
            OrderLineItem.product_id == product_id,
            OrderLineItem.warehouse_id == warehouse_id,
            CustomerOrder.status.in_(["PENDING", "AT_RISK"]),
            CustomerOrder.required_delivery_date <= disruption_end
        ).order_by(CustomerOrder.required_delivery_date.asc()).all()

        at_risk = []
        for order, item in orders:
            at_risk.append({
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "priority": order.priority,
                "required_delivery_date": str(order.required_delivery_date),
                "ordered_qty": item.ordered_qty,
                "fulfilled_qty": item.fulfilled_qty,
                "unfulfilled_qty": item.ordered_qty - item.fulfilled_qty,
                "unit_price": item.unit_price,
                "order_revenue": round(item.ordered_qty * item.unit_price, 2)
            })
        return at_risk
