# Self-Improvement Engine & Experimentation Methodology

## 1. Grounded Empirical Improvement Lifecycle
ORBIT does not allow an LLM to rewrite its own source code or make unverified prompt adjustments. Instead, it employs a controlled, reproducible scientific experimentation pipeline:

```
[Observe Historical Traces]
         │
         ▼
[Diagnose Operational Inefficiencies]
         │
         ▼
[Formulate Versioned Candidate Parameters]
         │
         ▼
[Run Controlled Benchmark Holdout Scenarios]
         │
         ▼
[Compute Multi-Dimensional Statistical Comparison]
         │
         ▼
[Safety Gate Evaluation & Human-Controlled Promotion]
```

## 2. Decision Policy Parameters
Policies govern the weights used during automated vendor scoring and inventory rebalancing:
- `supplier_reliability_weight` ($W_{\text{rel}}$): Relative importance of vendor OTIF delivery rate (0.0 to 1.0).
- `lead_time_weight` ($W_{\text{lead}}$): Relative importance of fast delivery turnaround.
- `unit_price_weight` ($W_{\text{price}}$): Relative importance of lowest wholesale acquisition cost.
- `safety_stock_buffer_ratio`: Multiplier applied to baseline buffer during heightened uncertainty.

## 3. Fixed Holdout Benchmark Suite
Candidate policies are evaluated against fixed benchmark scenarios:
1. `BENCH-01`: Severe 7-Day Tier-1 Supplier Delay (Apex Industrial Components, 150 units).
2. `BENCH-02`: Sudden 45% Demand Surge in Chicago Distribution Center (90 units shortfall).
3. `BENCH-03`: Concurrent Multi-Supplier Bottleneck (220 units across multiple regional nodes).

## 4. Multi-Dimensional Promotion Criteria
A candidate policy is eligible for promotion to `ACTIVE_PRODUCTION` only if:
1. **Stockout Reduction**: Total stockout units reduced by $\ge 25\%$.
2. **SLA Preservation**: Service level agreement compliance rate is maintained or improved.
3. **Cost Ceiling**: Total recovery expenditure increase does not exceed $15\%$.
4. **Human Authorization**: An Operations Lead or Executive provides explicit sign-off in the UI.

Rollback to previous stable baselines (`v1.0.0-baseline`) can be executed with a single click.
