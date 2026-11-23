import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models.supply_chain import (
    Warehouse, Supplier, ProductCategory, Product, SupplierProduct,
    Inventory, CustomerOrder, OrderLineItem, PurchaseOrder, POLineItem,
    DemandHistory, OperationalIncident
)
from app.models.policy import DecisionPolicy

def seed_database(db: Session) -> None:
    """
    Seeds a rich, deterministic, interconnected supply chain dataset.
    Ensures that every entity relationship is sound and reproducible.
    """
    # Check if already seeded
    if db.query(Warehouse).first():
        return

    random.seed(42)  # Deterministic seed for reproducible evaluation

    # 1. Warehouses
    warehouses_data = [
        {"code": "WH-CHI", "name": "Midwest Distribution Center", "location": "Chicago, IL", "capacity_units": 25000, "current_utilization": 68.5, "operating_cost_per_day": 850.0},
        {"code": "WH-DFW", "name": "South Central Logistics Hub", "location": "Dallas, TX", "capacity_units": 30000, "current_utilization": 74.2, "operating_cost_per_day": 920.0},
        {"code": "WH-ATL", "name": "Southeast Fulfillment Facility", "location": "Atlanta, GA", "capacity_units": 20000, "current_utilization": 61.0, "operating_cost_per_day": 780.0},
    ]
    warehouses = [Warehouse(**w) for w in warehouses_data]
    db.add_all(warehouses)
    db.flush()

    # 2. Suppliers
    suppliers_data = [
        {"code": "SUP-APEX", "name": "Apex Industrial Components", "tier": "Tier 1", "reliability_score": 0.94, "avg_lead_time_days": 7, "on_time_delivery_rate": 0.93, "quality_rating": 4.9, "contact_email": "ops@apexindustrial.com"},
        {"code": "SUP-NEXUS", "name": "Nexus Precision Dynamics", "tier": "Tier 1", "reliability_score": 0.98, "avg_lead_time_days": 3, "on_time_delivery_rate": 0.97, "quality_rating": 4.95, "contact_email": "expedite@nexusprecision.com"},
        {"code": "SUP-GLOBAL", "name": "Global Logistics & Parts", "tier": "Tier 2", "reliability_score": 0.86, "avg_lead_time_days": 12, "on_time_delivery_rate": 0.84, "quality_rating": 4.4, "contact_email": "orders@globalparts.com"},
        {"code": "SUP-VANGUARD", "name": "Vanguard Micro-Controls", "tier": "Tier 1", "reliability_score": 0.96, "avg_lead_time_days": 5, "on_time_delivery_rate": 0.95, "quality_rating": 4.85, "contact_email": "sales@vanguardcontrols.com"},
        {"code": "SUP-TITAN", "name": "Titan Heavy Assemblies", "tier": "Tier 2", "reliability_score": 0.90, "avg_lead_time_days": 9, "on_time_delivery_rate": 0.89, "quality_rating": 4.6, "contact_email": "contracts@titanassemblies.com"},
    ]
    suppliers = [Supplier(**s) for s in suppliers_data]
    db.add_all(suppliers)
    db.flush()

    # 3. Product Categories
    categories_data = [
        {"name": "Industrial Automation", "description": "Motors, actuators, drives and robotic motion components"},
        {"name": "Fluid & Power Transmission", "description": "High-pressure valves, pumps, bearings and hydraulics"},
        {"name": "Electrical & Control", "description": "PLCs, sensors, relays, inverters and telemetry controllers"},
    ]
    categories = [ProductCategory(**c) for c in categories_data]
    db.add_all(categories)
    db.flush()

    # 4. Products
    products_data = [
        # Cat 1: Industrial Automation
        {"sku": "P-MOT-100", "name": "High-Torque AC Servo Motor 750W", "category_id": categories[0].id, "unit_cost": 185.0, "selling_price": 340.0, "safety_stock": 40, "reorder_point": 90, "min_order_qty": 25},
        {"sku": "P-ACT-150", "name": "Linear Electric Actuator 12V", "category_id": categories[0].id, "unit_cost": 95.0, "selling_price": 175.0, "safety_stock": 50, "reorder_point": 110, "min_order_qty": 30},
        {"sku": "P-GRB-180", "name": "Planetary Precision Gearbox 10:1", "category_id": categories[0].id, "unit_cost": 140.0, "selling_price": 260.0, "safety_stock": 35, "reorder_point": 80, "min_order_qty": 20},
        {"sku": "P-ROB-190", "name": "SCARA Robotic Arm Joint Bearing", "category_id": categories[0].id, "unit_cost": 210.0, "selling_price": 420.0, "safety_stock": 25, "reorder_point": 60, "min_order_qty": 15},
        
        # Cat 2: Fluid & Power Transmission
        {"sku": "P-VLV-200", "name": "Smart Proportional Flow Control Valve", "category_id": categories[1].id, "unit_cost": 115.0, "selling_price": 220.0, "safety_stock": 45, "reorder_point": 100, "min_order_qty": 30},
        {"sku": "P-PMP-220", "name": "Variable Speed Hydraulic Pump 5kW", "category_id": categories[1].id, "unit_cost": 290.0, "selling_price": 580.0, "safety_stock": 20, "reorder_point": 50, "min_order_qty": 10},
        {"sku": "P-HYD-250", "name": "Heavy-Duty Dual Action Cylinder", "category_id": categories[1].id, "unit_cost": 160.0, "selling_price": 310.0, "safety_stock": 30, "reorder_point": 70, "min_order_qty": 20},
        {"sku": "P-BRG-280", "name": "Ceramic Deep Groove Ball Bearing", "category_id": categories[1].id, "unit_cost": 42.0, "selling_price": 88.0, "safety_stock": 100, "reorder_point": 250, "min_order_qty": 50},

        # Cat 3: Electrical & Control
        {"sku": "P-PLC-300", "name": "Modular Industrial PLC Controller", "category_id": categories[2].id, "unit_cost": 320.0, "selling_price": 650.0, "safety_stock": 25, "reorder_point": 55, "min_order_qty": 15},
        {"sku": "P-SEN-320", "name": "Laser Distance Proximity Sensor", "category_id": categories[2].id, "unit_cost": 65.0, "selling_price": 135.0, "safety_stock": 80, "reorder_point": 180, "min_order_qty": 40},
        {"sku": "P-INV-350", "name": "Variable Frequency Drive 15HP Inverter", "category_id": categories[2].id, "unit_cost": 410.0, "selling_price": 820.0, "safety_stock": 15, "reorder_point": 40, "min_order_qty": 10},
        {"sku": "P-REL-380", "name": "High-Current Solid State Relay 50A", "category_id": categories[2].id, "unit_cost": 32.0, "selling_price": 72.0, "safety_stock": 90, "reorder_point": 200, "min_order_qty": 50},
    ]
    products = [Product(**p) for p in products_data]
    db.add_all(products)
    db.flush()

    # 5. Supplier-Product Matrix (Alternative sourcing options)
    # Target Disruption Product: P-MOT-100 (Servo Motor)
    # Primary: SUP-APEX ($185, 7 days)
    # Fast Alt: SUP-NEXUS ($205, 3 days)
    # Economy Alt: SUP-GLOBAL ($175, 12 days)
    sp_entries = [
        # P-MOT-100 (Servo Motor)
        SupplierProduct(supplier_id=suppliers[0].id, product_id=products[0].id, unit_cost=185.0, lead_time_days=7, min_order_qty=25, max_capacity_per_week=400, is_primary=True),
        SupplierProduct(supplier_id=suppliers[1].id, product_id=products[0].id, unit_cost=205.0, lead_time_days=3, min_order_qty=20, max_capacity_per_week=250, is_primary=False),
        SupplierProduct(supplier_id=suppliers[2].id, product_id=products[0].id, unit_cost=172.0, lead_time_days=12, min_order_qty=50, max_capacity_per_week=500, is_primary=False),

        # P-ACT-150
        SupplierProduct(supplier_id=suppliers[0].id, product_id=products[1].id, unit_cost=95.0, lead_time_days=6, min_order_qty=30, max_capacity_per_week=300, is_primary=True),
        SupplierProduct(supplier_id=suppliers[3].id, product_id=products[1].id, unit_cost=102.0, lead_time_days=4, min_order_qty=25, max_capacity_per_week=200, is_primary=False),

        # P-VLV-200 (Smart Flow Valve)
        SupplierProduct(supplier_id=suppliers[0].id, product_id=products[4].id, unit_cost=115.0, lead_time_days=7, min_order_qty=30, max_capacity_per_week=350, is_primary=True),
        SupplierProduct(supplier_id=suppliers[1].id, product_id=products[4].id, unit_cost=128.0, lead_time_days=3, min_order_qty=25, max_capacity_per_week=200, is_primary=False),
        SupplierProduct(supplier_id=suppliers[4].id, product_id=products[4].id, unit_cost=112.0, lead_time_days=8, min_order_qty=40, max_capacity_per_week=400, is_primary=False),

        # P-PLC-300
        SupplierProduct(supplier_id=suppliers[3].id, product_id=products[8].id, unit_cost=320.0, lead_time_days=5, min_order_qty=15, max_capacity_per_week=150, is_primary=True),
        SupplierProduct(supplier_id=suppliers[1].id, product_id=products[8].id, unit_cost=345.0, lead_time_days=3, min_order_qty=10, max_capacity_per_week=100, is_primary=False),

        # Other products mapped to appropriate suppliers
        SupplierProduct(supplier_id=suppliers[4].id, product_id=products[5].id, unit_cost=290.0, lead_time_days=9, min_order_qty=10, max_capacity_per_week=120, is_primary=True),
        SupplierProduct(supplier_id=suppliers[0].id, product_id=products[6].id, unit_cost=160.0, lead_time_days=7, min_order_qty=20, max_capacity_per_week=200, is_primary=True),
        SupplierProduct(supplier_id=suppliers[2].id, product_id=products[7].id, unit_cost=42.0, lead_time_days=10, min_order_qty=50, max_capacity_per_week=1000, is_primary=True),
    ]
    db.add_all(sp_entries)
    db.flush()

    # 6. Inventory Records
    # Disruption Context:
    # In WH-CHI (Chicago), P-MOT-100 on hand is critically low (only 18 units, safety stock is 40).
    # But in WH-DFW (Dallas), P-MOT-100 has a healthy surplus (115 units on hand).
    # This allows ORBIT to discover the inter-warehouse transfer option!
    for p in products:
        for w in warehouses:
            if p.sku == "P-MOT-100" and w.code == "WH-CHI":
                on_hand = 18  # Critical stockout cliff!
                reserved = 12
            elif p.sku == "P-MOT-100" and w.code == "WH-DFW":
                on_hand = 120  # Significant surplus (> safety stock 40 * 1.2 = 48)
                reserved = 20
            elif p.sku == "P-MOT-100" and w.code == "WH-ATL":
                on_hand = 45
                reserved = 10
            else:
                on_hand = random.randint(int(p.safety_stock * 1.1), int(p.reorder_point * 1.5))
                reserved = random.randint(5, max(6, int(on_hand * 0.25)))

            inv = Inventory(
                warehouse_id=w.id,
                product_id=p.id,
                on_hand_qty=on_hand,
                reserved_qty=reserved,
                allocated_qty=reserved,
                in_transit_qty=0
            )
            db.add(inv)
    db.flush()

    # 7. Demand History (Past 30 days)
    today = date.today()
    for p in products:
        base_demand = 8.0 if p.unit_cost > 200 else 16.0
        for w in warehouses:
            for day_idx in range(30, 0, -1):
                hist_date = today - timedelta(days=day_idx)
                # Introduce slight weekday vs weekend seasonality + gaussian noise
                weekday_factor = 1.2 if hist_date.weekday() < 5 else 0.6
                demand_val = max(1, int(round(base_demand * weekday_factor + random.gauss(0, 2.5))))
                dh = DemandHistory(
                    product_id=p.id,
                    warehouse_id=w.id,
                    date=hist_date,
                    demand_qty=demand_val
                )
                db.add(dh)
    db.flush()

    # 8. Customer Orders
    # At-risk customer orders scheduled to be fulfilled from Chicago DC for P-MOT-100 in next 2-6 days
    customer_names = [
        "Siemens Mobility North America", "Boeing Commercial Aerostructures", "Tesla Gigafactory Texas",
        "Honeywell Aerospace", "Caterpillar Manufacturing", "John Deere Harvester Works",
        "General Electric Healthcare", "Emerson Process Automation", "ABB Robotics Division",
        "Rockwell Automation Global", "Lockheed Martin Missiles", "Schneider Electric Facilities"
    ]

    orders_count = 0
    # Create specific at-risk orders for P-MOT-100 in Chicago
    target_prod = products[0]  # P-MOT-100
    chicago_wh = warehouses[0] # WH-CHI

    urgent_order_configs = [
        {"cust": "Boeing Commercial Aerostructures", "days_out": 2, "qty": 10, "pri": "VIP"},
        {"cust": "Rockwell Automation Global", "days_out": 3, "qty": 15, "pri": "VIP"},
        {"cust": "Siemens Mobility North America", "days_out": 4, "qty": 12, "pri": "EXPEDITED"},
        {"cust": "Caterpillar Manufacturing", "days_out": 5, "qty": 14, "pri": "STANDARD"},
        {"cust": "Emerson Process Automation", "days_out": 6, "qty": 8, "pri": "STANDARD"},
    ]

    for cfg in urgent_order_configs:
        orders_count += 1
        ord_num = f"ORD-2026-{1000 + orders_count}"
        rev = round(cfg["qty"] * target_prod.selling_price, 2)
        co = CustomerOrder(
            order_number=ord_num,
            customer_name=cfg["cust"],
            order_date=today - timedelta(days=3),
            required_delivery_date=today + timedelta(days=cfg["days_out"]),
            status="AT_RISK",
            priority=cfg["pri"],
            total_revenue=rev
        )
        db.add(co)
        db.flush()

        item = OrderLineItem(
            order_id=co.id,
            product_id=target_prod.id,
            warehouse_id=chicago_wh.id,
            ordered_qty=cfg["qty"],
            fulfilled_qty=0,
            unit_price=target_prod.selling_price
        )
        db.add(item)

    # Add other baseline customer orders across network
    for i in range(15):
        orders_count += 1
        ord_num = f"ORD-2026-{1000 + orders_count}"
        co_prod = random.choice(products)
        co_wh = random.choice(warehouses)
        co_qty = random.randint(5, 20)
        co_rev = round(co_qty * co_prod.selling_price, 2)
        co = CustomerOrder(
            order_number=ord_num,
            customer_name=random.choice(customer_names),
            order_date=today - timedelta(days=random.randint(1, 4)),
            required_delivery_date=today + timedelta(days=random.randint(4, 14)),
            status="PENDING",
            priority=random.choice(["STANDARD", "STANDARD", "EXPEDITED", "VIP"]),
            total_revenue=co_rev
        )
        db.add(co)
        db.flush()

        item = OrderLineItem(
            order_id=co.id,
            product_id=co_prod.id,
            warehouse_id=co_wh.id,
            ordered_qty=co_qty,
            fulfilled_qty=0,
            unit_price=co_prod.selling_price
        )
        db.add(item)
    db.flush()

    # 9. Upstream Purchase Orders (including the disrupted PO)
    # PRIMARY DISRUPTION PO:
    # PO-2026-8812 from Apex Industrial to Chicago DC for 150 units of P-MOT-100
    # Originally expected tomorrow, delayed by 7 days due to component shortage!
    apex_supplier = suppliers[0]
    disrupted_po = PurchaseOrder(
        po_number="PO-2026-8812",
        supplier_id=apex_supplier.id,
        warehouse_id=chicago_wh.id,
        order_date=today - timedelta(days=6),
        expected_delivery_date=today + timedelta(days=1),
        revised_delivery_date=today + timedelta(days=8),
        delay_days=7,
        status="DELAYED",
        total_cost=round(150 * 185.0, 2)
    )
    db.add(disrupted_po)
    db.flush()

    po_item = POLineItem(
        po_id=disrupted_po.id,
        product_id=target_prod.id,
        qty=150,
        unit_cost=185.0
    )
    db.add(po_item)

    # Add other normal POs in flight
    normal_pos = [
        {"po": "PO-2026-8809", "sup": suppliers[3], "wh": warehouses[1], "prod": products[8], "qty": 40, "days": 3},
        {"po": "PO-2026-8810", "sup": suppliers[4], "wh": warehouses[2], "prod": products[5], "qty": 25, "days": 5},
    ]
    for npo in normal_pos:
        po_obj = PurchaseOrder(
            po_number=npo["po"],
            supplier_id=npo["sup"].id,
            warehouse_id=npo["wh"].id,
            order_date=today - timedelta(days=2),
            expected_delivery_date=today + timedelta(days=npo["days"]),
            status="IN_TRANSIT",
            total_cost=round(npo["qty"] * npo["prod"].unit_cost, 2)
        )
        db.add(po_obj)
        db.flush()
        db.add(POLineItem(po_id=po_obj.id, product_id=npo["prod"].id, qty=npo["qty"], unit_cost=npo["prod"].unit_cost))
    db.flush()

    # 10. Operational Incident (Primary Disruption Scenario)
    incident = OperationalIncident(
        incident_key="INC-2026-042",
        incident_type="SUPPLIER_DELAY",
        title="Severe 7-Day Inbound Delivery Delay from Apex Industrial Components",
        description="Supplier Apex Industrial reported sub-tier semiconductor wafer bottleneck delaying shipment PO-2026-8812 (150 units of P-MOT-100 High-Torque Servo Motor to Chicago DC). Delivery revised from tomorrow to +7 days.",
        severity="CRITICAL",
        status="OPEN",
        affected_supplier_id=apex_supplier.id,
        affected_warehouse_id=chicago_wh.id,
        detected_at=datetime.utcnow() - timedelta(hours=2),
        details_json={
            "po_number": "PO-2026-8812",
            "delay_days": 7,
            "product_sku": "P-MOT-100",
            "quantity_delayed": 150,
            "root_cause": "Sub-tier micro-bearing supplier strike and export customs hold",
            "confirmed": True
        }
    )
    db.add(incident)

    # 11. Initial Baseline Decision Policy
    baseline_policy = DecisionPolicy(
        version="v1.0.0-baseline",
        name="Cost-Prioritizing Baseline Policy",
        description="Standard procurement policy weighting unit price heavily (40%) and lead time (35%), with lower emphasis on supplier reliability (25%). Reorder threshold buffer is conservative.",
        parameters={
            "supplier_reliability_weight": 0.20,
            "lead_time_weight": 0.25,
            "unit_price_weight": 0.55,
            "min_supplier_reliability_threshold": 0.80,
            "safety_stock_buffer_ratio": 1.15,
            "expedite_cost_multiplier": 1.35,
            "transfer_cost_per_unit_km": 0.08
        },
        is_active=True
    )
    db.add(baseline_policy)

    db.commit()
    print("ORBIT Synthetic Business Dataset successfully seeded.")
