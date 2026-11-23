from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.supply_chain import Supplier, SupplierProduct, Product

class SupplierService:
    DEFAULT_POLICY_PARAMS = {
        "supplier_reliability_weight": 0.30,
        "lead_time_weight": 0.35,
        "unit_price_weight": 0.35,
        "min_supplier_reliability_threshold": 0.85
    }

    @staticmethod
    def calculate_supplier_score(
        reliability: float,
        lead_time_days: int,
        unit_price: float,
        max_lead_time: int = 21,
        max_unit_price: float = 500.0,
        policy_params: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Computes composite multi-attribute score (0.0 to 1.0) using bounded weights.
        Higher is better.
        """
        params = policy_params or SupplierService.DEFAULT_POLICY_PARAMS
        w_rel = params.get("supplier_reliability_weight", 0.30)
        w_lead = params.get("lead_time_weight", 0.35)
        w_price = params.get("unit_price_weight", 0.35)

        # Normalize lead time (shorter is better)
        lead_score = max(0.0, 1.0 - (float(lead_time_days) / float(max(1, max_lead_time))))
        # Normalize unit price (cheaper is better)
        price_score = max(0.0, 1.0 - (float(unit_price) / float(max(1.0, max_unit_price))))
        # Reliability score (higher is better)
        rel_score = min(1.0, max(0.0, float(reliability)))

        total_score = (w_rel * rel_score) + (w_lead * lead_score) + (w_price * price_score)
        return round(float(total_score), 4)

    @staticmethod
    def evaluate_alternative_suppliers(
        db: Session,
        product_id: int,
        exclude_supplier_id: Optional[int] = None,
        policy_params: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves and ranks all qualified suppliers for a given product
        using real records from the database.
        """
        params = policy_params or SupplierService.DEFAULT_POLICY_PARAMS
        min_rel = params.get("min_supplier_reliability_threshold", 0.85)

        query = db.query(SupplierProduct, Supplier, Product).join(
            Supplier, SupplierProduct.supplier_id == Supplier.id
        ).join(
            Product, SupplierProduct.product_id == Product.id
        ).filter(
            SupplierProduct.product_id == product_id
        )

        if exclude_supplier_id:
            query = query.filter(SupplierProduct.supplier_id != exclude_supplier_id)

        records = query.all()
        if not records:
            return []

        # Find max lead time and max price for normalization
        max_lead = max([sp.lead_time_days for sp, s, p in records] + [14])
        max_price = max([sp.unit_cost for sp, s, p in records] + [100.0])

        candidates = []
        for sp, s, p in records:
            score = SupplierService.calculate_supplier_score(
                reliability=s.reliability_score,
                lead_time_days=sp.lead_time_days,
                unit_price=sp.unit_cost,
                max_lead_time=max_lead,
                max_unit_price=max_price,
                policy_params=params
            )

            is_qualified = s.reliability_score >= min_rel

            candidates.append({
                "supplier_id": s.id,
                "supplier_code": s.code,
                "supplier_name": s.name,
                "tier": s.tier,
                "reliability_score": s.reliability_score,
                "on_time_delivery_rate": s.on_time_delivery_rate,
                "quality_rating": s.quality_rating,
                "lead_time_days": sp.lead_time_days,
                "unit_cost": sp.unit_cost,
                "min_order_qty": sp.min_order_qty,
                "max_capacity_per_week": sp.max_capacity_per_week,
                "is_primary": sp.is_primary,
                "composite_score": score,
                "meets_safety_threshold": is_qualified
            })

        # Sort by composite score descending
        candidates.sort(key=lambda x: x["composite_score"], reverse=True)
        return candidates
