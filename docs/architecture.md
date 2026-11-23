# ORBIT Technical Architecture

## 1. System Vision
ORBIT is an enterprise-grade autonomous multi-agent business operations intelligence platform designed to eliminate the operational burden of supply chain disruptions. Built with a strict principle of **minimum user effort** and **grounded numerical decision intelligence**, ORBIT translates natural-language operational objectives into structured multi-agent workflows while delegating numerical, cost, and constraint calculations to deterministic Python algorithms.

## 2. Core Components

### A. FastAPI Backend Application
- **Path**: `backend/app/`
- Serves typed REST APIs under `/api/dashboard`, `/api/supply-chain`, `/api/incidents`, `/api/scenarios`, `/api/workflows`, `/api/improvement`, and `/api/observability`.
- Manages SQLAlchemy 2.0 ORM persistence with zero-dependency SQLite local execution and production PostgreSQL compatibility.

### B. Multi-Agent Orchestrator (LangGraph)
- **Path**: `backend/app/orchestration/graph.py`
- Compiled state graph with 7 sequential and conditional agent nodes:
  1. `SupervisorAgent`: Classifies task intent, decomposes subtasks, constructs execution DAG.
  2. `DetectionAgent`: Identifies delivery delays, anomalous PO records, and categorizes information into Confirmed, Estimated, Missing, and Assumed.
  3. `ImpactAnalysisAgent`: Calculates inventory runway days, exact stockout date, and at-risk customer order revenue.
  4. `DemandForecastingAgent`: Fits statistical time-series models (SMA, Holt-Winters linear trend) with MAPE/MAE error metrics.
  5. `SupplierIntelligenceAgent`: Evaluates qualified alternative vendors, lead times, MOQ, and reliability scores.
  6. `OptimizationAgent`: Formulates 3 competing mathematical recovery strategies (Expedited Alternative, Balanced Transfer & Reorder, Cost-Minimalist).
  7. `VerificationAgent`: Audits inventory mass conservation, capacity bounds, and lead-time constraints.
  8. `ExecutionAgent`: Executes authorized actions across simulated ERP/WMS.
  9. `ImprovementAgent`: Conducts reproducible benchmark experiments across versioned decision policies.

### C. Operations Command Center Frontend
- **Path**: `frontend/src/`
- Modern React 19 + TypeScript + Vite + Tailwind CSS v4 application.
- 8 specialized operational cockpits:
  1. Command Center: High-level KPIs, storage utilization, vendor reliability matrix.
  2. Task Console: Natural language objective input, scenario launcher, executive summaries.
  3. Live Agent Execution: Visual pipeline DAG, execution durations, tool calls inspector.
  4. Supply Chain Intelligence: Interactive inventory ledger, vendor scores, demand charts.
  5. Disruption Investigation: Incident root cause, 4-quadrant certainty grid.
  6. Recovery Plan & Approvals: Side-by-side strategy trade-off cards, human approval gates.
  7. Self-Improvement Lab: Policy parameter formulation, benchmark simulation, promotion/rollback.
  8. Observability & Traces: Execution telemetry, latency distributions, token costs.
