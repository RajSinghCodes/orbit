from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.workflow import Workflow, AgentTrace

router = APIRouter(prefix="/observability", tags=["System Observability"])

@router.get("/metrics")
def get_observability_metrics(db: Session = Depends(get_db)):
    """
    Computes system observability, agent latency distributions, token usage,
    and tool call metrics from actual execution records.
    """
    total_workflows = db.query(Workflow).count()
    completed_workflows = db.query(Workflow).filter(
        Workflow.status.in_(["COMPLETED", "REQUIRES_APPROVAL"])
    ).count()
    failed_workflows = db.query(Workflow).filter(Workflow.status == "FAILED").count()

    success_rate = round((completed_workflows / max(1, total_workflows)) * 100.0, 1) if total_workflows else 100.0

    # Traces analysis
    traces = db.query(AgentTrace).all()
    total_traces = len(traces)
    total_tokens = sum([t.token_usage for t in traces])
    # Estimated model cost: ~$0.15 per million tokens for Gemini Flash / lightweight models
    est_cost = round((total_tokens / 1_000_000.0) * 0.15, 4)

    durations = [t.duration_ms for t in traces if t.duration_ms > 0]
    avg_latency_ms = round(sum(durations) / max(1, len(durations)), 1) if durations else 0.0

    # Breakdown by agent
    agent_counts: Dict[str, Dict[str, Any]] = {}
    total_tools_called = 0

    for t in traces:
        name = t.agent_name
        tools_in_trace = len(t.tool_calls) if t.tool_calls else 0
        total_tools_called += tools_in_trace

        if name not in agent_counts:
            agent_counts[name] = {
                "executions": 0,
                "total_duration_ms": 0.0,
                "total_tokens": 0,
                "tool_calls": 0,
                "failures": 0
            }
        agent_counts[name]["executions"] += 1
        agent_counts[name]["total_duration_ms"] += t.duration_ms
        agent_counts[name]["total_tokens"] += t.token_usage
        agent_counts[name]["tool_calls"] += tools_in_trace
        if t.status == "FAILED":
            agent_counts[name]["failures"] += 1

    agent_summary = []
    for name, stats in agent_counts.items():
        exec_count = stats["executions"]
        agent_summary.append({
            "agent_name": name,
            "execution_count": exec_count,
            "avg_latency_ms": round(stats["total_duration_ms"] / max(1, exec_count), 1),
            "total_tokens": stats["total_tokens"],
            "tool_calls_count": stats["tool_calls"],
            "failures": stats["failures"]
        })

    return {
        "total_workflows": total_workflows,
        "completed_workflows": completed_workflows,
        "failed_workflows": failed_workflows,
        "success_rate_pct": success_rate,
        "avg_agent_latency_ms": avg_latency_ms,
        "total_tokens_consumed": total_tokens,
        "estimated_llm_cost_usd": est_cost,
        "total_tools_invoked": total_tools_called,
        "agent_performance_breakdown": agent_summary
    }
