# ORBIT — Autonomous Business Operations Intelligence

> **Production-grade multi-agent operations intelligence platform designed to eliminate the operational burden of supply chain disruptions.**

ORBIT combines **LangGraph multi-agent orchestration** with **grounded mathematical optimization** to autonomously investigate operational bottlenecks, calculate inventory depletion timelines, forecast future demand, evaluate competing recovery strategies, enforce human-in-the-loop authorization gates, execute simulated corrective operations, and improve operational policies through controlled experimentation.

---

## 🌟 Key Capabilities

1. **Autonomous Operational Investigation**: Translates high-level natural language objectives into structured DAG workflows.
2. **Grounded Numerical Decision Intelligence**: Prevents LLM mathematical hallucinations by delegating stockout runways, safety stock buffers, costs, and multi-attribute supplier scoring to deterministic Python services.
3. **Multi-Strategy Optimization**: Generates and compares 3 competing recovery strategies side-by-side:
   - *Strategy 1*: Rapid Expedited Alternative Sourcing (Maximum SLA Protection)
   - *Strategy 2*: Balanced Inter-Warehouse Transfer & Split Sourcing (Cost-Optimal Recommended)
   - *Strategy 3*: Cost-Minimalist VIP Protection (Maximum Short-Term Cash Conservation)
4. **Human-in-the-Loop Governance**: Segregates actions into risk tiers. All external financial commitments and inventory movements require explicit human approval.
5. **Closed-Loop Self-Improvement Engine**: Diagnoses inefficiencies in historical executions, proposes versioned candidate parameters, runs controlled experiments against benchmark holdout suites, and enforces safety gates before production promotion.
6. **Full System Observability**: Captures execution traces, agent durations in milliseconds, token expenditures, and tool invocation parameters.

---

## 🏗️ Architecture Overview

```
                                ┌──────────────────────────────────────────────┐
                                │             ORBIT Web Command Center          │
                                │   React 19 · TypeScript · Vite · Tailwind CSS │
                                └──────────────────────┬───────────────────────┘
                                                       │ REST / JSON API
                                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             FastAPI Backend Application                                      │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                      LangGraph Multi-Agent Orchestrator                                      │
│                                                                                                              │
│    ┌──────────────────┐           ┌──────────────────┐            ┌───────────────────────────┐              │
│    │ Supervisor Agent │ ───────▶  │  Detection Agent │  ────────▶ │   Impact Analysis Agent   │              │
│    └────────┬─────────┘           └──────────────────┘            └─────────────┬─────────────┘              │
│             │                                                                   │                            │
│             ▼                                                                   ▼                            │
│    ┌──────────────────┐           ┌──────────────────┐            ┌───────────────────────────┐              │
│    │ Demand Forecast  │ ───────▶  │ Supplier Intel   │  ────────▶ │    Optimization Agent     │              │
│    └──────────────────┘           └──────────────────┘            └─────────────┬─────────────┘              │
│                                                                                 │                            │
│             ┌───────────────────────────────────────────────────────────────────┘                            │
│             ▼                                                                                                │
│    ┌──────────────────┐           ┌──────────────────┐            ┌───────────────────────────┐              │
│    │ Human Approval   │ ───────▶  │ Execution Agent  │  ────────▶ │    Verification Agent     │              │
│    │ (Action Review)  │           │ (Simulated ERP)  │            │ (Mass Balance & Invariant)│              │
│    └──────────────────┘           └──────────────────┘            └─────────────┬─────────────┘              │
│                                                                                 │                            │
│                                                                                 ▼                            │
│                                                                   ┌───────────────────────────┐              │
│                                                                   │     Improvement Agent     │              │
│                                                                   │  (Benchmark Experiments)  │              │
│                                                                   └───────────────────────────┘              │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│               Core Services & Decision Engines (Deterministic, Non-Hallucinated Math)                        │
│    • Inventory Runway Engine          • Demand Forecasting (Holt-Winters/SMA) • Mathematical Optimizer       │
│    • Supplier Scoring Engine          • Scenario Simulation Engine            • Self-Improvement Benchmark   │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                    Storage & Persistence Layer                                               │
│    • SQLAlchemy 2.0 ORM               • SQLite (Zero-Config Dev) / PostgreSQL • Audit Trace Store            │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart (Zero Configuration)

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm

### 1. Start Backend
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*The database and realistic synthetic supply chain dataset will initialize and seed automatically.*
Interactive API documentation available at: `http://localhost:8000/docs`

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Automated Testing Suite

ORBIT includes a comprehensive test suite covering deterministic calculations, mathematical constraints, LangGraph state execution, and the self-improvement promotion engine:

```bash
cd backend
python -m pytest -v
```

Output:
```
tests/test_calculations.py::test_inventory_runway_calculation PASSED
tests/test_calculations.py::test_stockout_risk_classification PASSED
tests/test_calculations.py::test_forecasting_metrics PASSED
tests/test_calculations.py::test_supplier_scoring PASSED
tests/test_workflow.py::test_full_langgraph_disruption_workflow PASSED
tests/test_workflow.py::test_self_improvement_experiment_and_promotion PASSED
```

---

## 🧭 The 8 Command Center Cockpits

1. **Operations Command Center**: Executive overview of total inventory valuation, active disruptions, at-risk customer revenue, warehouse capacities, and vendor OTIF rates.
2. **ORBIT Task Console**: Autonomous operational cockpit where users input high-level objectives or trigger benchmark scenarios.
3. **Live Agent Execution**: Visual LangGraph DAG displaying runtime latencies, token consumption, and an interactive tool calls inspector.
4. **Supply Chain Intelligence**: Interactive inventory ledger with stockout runways, vendor reliability matrices, and historical sales trends.
5. **Disruption Investigation**: Root-cause diagnostic workspace with four-quadrant information certainty classification (Confirmed, Estimated, Missing, Assumed).
6. **Recovery & Approvals**: Side-by-side trade-off comparison of the 3 competing recovery plans with human-in-the-loop action approval controls and simulated ERP dispatch.
7. **Self-Improvement Lab**: Empirical policy experimentation workspace displaying baseline vs candidate policies, benchmark holdout outcomes, and promotion/rollback gates.
8. **Observability & Traces**: System telemetry dashboards showing latency distributions, token costs, tool invocation counts, and historical workflow replay.

---

## 🐳 Docker Deployment

Run the complete multi-tier stack (PostgreSQL, FastAPI backend, Nginx frontend) via Docker Compose:
```bash
docker-compose up --build -d
```
Access at `http://localhost`.

---

## 📄 License
MIT License. Built for Forward Deployed Engineering & Applied AI Architecture demonstrations.
