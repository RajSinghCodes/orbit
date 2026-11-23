import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.services.forecasting_service import ForecastingService
from app.services.trace_service import TraceService

class DemandForecastingAgent:
    """
    Demand Forecasting Agent:
    - Analyzes historical sales and order history.
    - Fits statistical forecasting baselines (SMA and Holt-Winters linear trend).
    - Computes forecast error metrics (MAE, MAPE, RMSE).
    - Generates 14-day projection with 95% confidence intervals.
    """
    NAME = "Demand Forecasting Agent"

    @classmethod
    def execute(cls, state: OrbitWorkflowState, db: Session) -> Dict[str, Any]:
        start_time = time.time()
        workflow_id = state.get("workflow_id", 1)
        disruption = state.get("disruption_data", {})

        prod_id = disruption.get("affected_product_id", 1)
        wh_id = disruption.get("affected_warehouse_id", 1)

        # Generate deterministic demand forecast
        forecast_result = ForecastingService.generate_product_forecast(
            db=db,
            product_id=prod_id,
            warehouse_id=wh_id,
            horizon_days=14
        )

        tool_calls = [
            {
                "tool_name": "fit_holt_winters_forecast",
                "arguments": {"product_id": prod_id, "warehouse_id": wh_id, "horizon": 14},
                "result": {
                    "model": forecast_result["model_type"],
                    "avg_daily_demand": forecast_result["avg_daily_demand"],
                    "mape": forecast_result["evaluation_metrics"]["mape"]
                }
            }
        ]

        duration_ms = (time.time() - start_time) * 1000.0

        TraceService.record_trace(
            db=db,
            workflow_id=workflow_id,
            agent_name=cls.NAME,
            task="Fit statistical time-series models and calculate forecast uncertainty",
            input_state={"product_id": prod_id, "warehouse_id": wh_id},
            output_state={"forecast_data": forecast_result},
            tool_calls=tool_calls,
            duration_ms=duration_ms,
            token_usage=165
        )

        return {"forecast_data": forecast_result, "current_step": "Supplier Intelligence Agent Dispatched"}
