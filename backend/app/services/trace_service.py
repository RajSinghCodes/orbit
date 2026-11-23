import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.workflow import AgentTrace

class TraceService:
    @staticmethod
    def record_trace(
        db: Session,
        workflow_id: int,
        agent_name: str,
        task: str,
        input_state: Dict[str, Any],
        output_state: Dict[str, Any],
        tool_calls: List[Dict[str, Any]],
        duration_ms: float,
        token_usage: int = 0,
        status: str = "COMPLETED",
        error_message: Optional[str] = None
    ) -> AgentTrace:
        """
        Records an observable, immutable agent execution trace in the database.
        Includes tool invocations, inputs, outputs, runtime, and token cost.
        """
        trace = AgentTrace(
            workflow_id=workflow_id,
            agent_name=agent_name,
            task=task,
            status=status,
            input_state=input_state,
            output_state=output_state,
            tool_calls=tool_calls,
            duration_ms=round(duration_ms, 2),
            token_usage=token_usage,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)
        return trace
