# System Evaluation & Engineering Metrics

ORBIT measures system performance across 12 empirical dimensions calculated directly from actual execution records:

| Metric | How It Is Calculated | Target Benchmark |
| :--- | :--- | :--- |
| **Task Completion Rate** | Ratio of workflows reaching `COMPLETED` or `REQUIRES_APPROVAL` without unhandled exception | $\ge 98.0\%$ |
| **Recommendation Feasibility** | Verification checks passed without constraint violations | $100\%$ |
| **Average Recovery Cost** | Total simulated purchasing, expedited freight, and transfer expenses | Minimal feasible |
| **Stockout Risk Score** | Estimated probability of on-hand inventory exhausting prior to replenishment | $\le 10\%$ for recommended |
| **Orders Protected Rate** | Percentage of at-risk customer orders fulfilled within SLA window | $\ge 95\%$ |
| **Forecasting Error (MAPE)** | $\frac{1}{n} \sum \left\vert \frac{Actual - Forecast}{Actual} \right\vert \times 100$ | $\le 15\%$ |
| **Forecasting Error (MAE)** | $\frac{1}{n} \sum \vert Actual - Forecast \vert$ | $\le 2.0$ units |
| **Constraint Violations** | Invariant infractions (negative inventory, exceeding warehouse capacity) | $0$ violations |
| **Average Workflow Latency** | End-to-end execution runtime through all LangGraph agents | $\le 500$ ms (deterministic) |
| **Token Usage Per Task** | Sum of input and output tokens consumed across agent steps | $\le 2,500$ tokens |
| **Estimated LLM Cost** | Approximate API cost based on standard model pricing tier | $\le \$0.001$ / workflow |
| **Self-Improvement Gain** | Measured percentage reduction in stockout units on holdout benchmark suite | $\ge 50\%$ gain |
