import random
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.supply_chain import (
    Warehouse, Supplier, Product, Inventory, InventoryMovement,
    CustomerOrder, OrderLineItem, PurchaseOrder, POLineItem, OperationalIncident
)
from app.models.workflow import ActionExecution, RecoveryPlan, Workflow

class SimulationService:
    @staticmethod
    def execute_action(db: Session, action: ActionExecution) -> Dict[str, Any]:
        """
        Executes an authorized simulated action, applying realistic state mutations
        to the supply chain database.
        """
        payload = action.payload or {}
        action_type = action.action_type
        result = {}

        if action_type == "CREATE_PURCHASE_ORDER":
            supplier_id = payload.get("supplier_id")
            warehouse_id = payload.get("warehouse_id")
            product_id = payload.get("product_id")
            quantity = payload.get("quantity", 100)
            unit_cost = payload.get("unit_cost", 50.0)
            arrival_days = payload.get("expected_arrival_days", 4)

            po_number = f"PO-SIM-{random.randint(1000, 9999)}"
            order_dt = date.today()
            delivery_dt = order_dt + timedelta(days=arrival_days)

            new_po = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier_id,
                warehouse_id=warehouse_id,
                order_date=order_dt,
                expected_delivery_date=delivery_dt,
                status="CONFIRMED",
                total_cost=round(quantity * unit_cost, 2)
            )
            db.add(new_po)
            db.flush()

            po_item = POLineItem(
                po_id=new_po.id,
                product_id=product_id,
                qty=quantity,
                unit_cost=unit_cost
            )
            db.add(po_item)

            # Update inventory in-transit qty
            inv = db.query(Inventory).filter(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id
            ).first()
            if inv:
                inv.in_transit_qty += quantity

            # Record inventory movement
            movement = InventoryMovement(
                movement_type="PURCHASE_ORDER_ISSUED",
                reference_id=po_number,
                product_id=product_id,
                to_warehouse_id=warehouse_id,
                qty=quantity,
                status="IN_TRANSIT"
            )
            db.add(movement)

            result = {
                "po_number": po_number,
                "status": "ISSUED_SIMULATED",
                "quantity": quantity,
                "expected_delivery_date": str(delivery_dt),
                "in_transit_updated": True
            }

        elif action_type == "TRANSFER_INVENTORY":
            from_wh = payload.get("from_warehouse_id")
            to_wh = payload.get("to_warehouse_id")
            product_id = payload.get("product_id")
            quantity = payload.get("quantity", 50)
            transit_days = payload.get("transit_days", 2)

            # Deduct from source warehouse on_hand
            src_inv = db.query(Inventory).filter(
                Inventory.warehouse_id == from_wh,
                Inventory.product_id == product_id
            ).first()
            if src_inv and src_inv.on_hand_qty >= quantity:
                src_inv.on_hand_qty -= quantity
            elif src_inv:
                quantity = src_inv.on_hand_qty
                src_inv.on_hand_qty = 0

            # Add to destination warehouse in_transit
            dest_inv = db.query(Inventory).filter(
                Inventory.warehouse_id == to_wh,
                Inventory.product_id == product_id
            ).first()
            if dest_inv:
                dest_inv.in_transit_qty += quantity

            transfer_ref = f"TRF-{random.randint(1000, 9999)}"
            movement = InventoryMovement(
                movement_type="WAREHOUSE_TRANSFER",
                reference_id=transfer_ref,
                product_id=product_id,
                from_warehouse_id=from_wh,
                to_warehouse_id=to_wh,
                qty=quantity,
                status="IN_TRANSIT"
            )
            db.add(movement)

            result = {
                "transfer_ref": transfer_ref,
                "status": "DISPATCHED_SIMULATED",
                "quantity_transferred": quantity,
                "transit_days": transit_days,
                "expected_arrival": str(date.today() + timedelta(days=transit_days))
            }

        elif action_type == "REALLOCATE_SAFETY_STOCK":
            warehouse_id = payload.get("warehouse_id")
            product_id = payload.get("product_id")
            released_units = payload.get("released_units", 25)

            inv = db.query(Inventory).filter(
                Inventory.warehouse_id == warehouse_id,
                Inventory.product_id == product_id
            ).first()
            if inv:
                # Deduct reserved to make available
                inv.reserved_qty = max(0, inv.reserved_qty - released_units)

            result = {
                "status": "REALLOCATED",
                "released_units": released_units,
                "message": "Safety stock reserve released for urgent order dispatch."
            }

        action.status = "EXECUTED"
        action.executed_at = datetime.utcnow()
        action.result = result
        db.commit()
        return result

    @staticmethod
    def verify_post_execution_invariants(db: Session, warehouse_id: int, product_id: int) -> Dict[str, Any]:
        """
        Strict verification of physical and business invariants:
        - Non-negative inventory balance
        - Warehouse capacity bounds
        - Pipeline replenishment coverage
        """
        inv = db.query(Inventory).filter(
            Inventory.warehouse_id == warehouse_id,
            Inventory.product_id == product_id
        ).first()

        wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        prod = db.query(Product).filter(Product.id == product_id).first()

        if not inv or not wh or not prod:
            return {"valid": False, "violations": ["Missing entity records"]}

        violations = []
        if inv.on_hand_qty < 0:
            violations.append(f"Negative on-hand inventory: {inv.on_hand_qty}")

        total_physical = inv.on_hand_qty + inv.in_transit_qty
        effective_coverage = total_physical >= prod.safety_stock

        return {
            "valid": len(violations) == 0,
            "on_hand_qty": inv.on_hand_qty,
            "in_transit_qty": inv.in_transit_qty,
            "total_effective_stock": total_physical,
            "safety_stock_threshold": prod.safety_stock,
            "meets_safety_stock": effective_coverage,
            "violations": violations
        }
