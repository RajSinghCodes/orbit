from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    objective = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, REQUIRES_APPROVAL
    scenario_key = Column(String(50), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_cost = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    risk_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)

    traces = relationship("AgentTrace", back_populates="workflow", cascade="all, delete-orphan")
    recovery_plans = relationship("RecoveryPlan", back_populates="workflow", cascade="all, delete-orphan")
    action_executions = relationship("ActionExecution", back_populates="workflow", cascade="all, delete-orphan")


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)  # Supervisor, Detection, Impact, Forecast, Supplier, Optimizer, Execution, Verification
    task = Column(String(255), nullable=False)
    status = Column(String(50), default="COMPLETED")  # STARTED, COMPLETED, FAILED, RETRIED
    input_state = Column(JSON, default=dict)
    output_state = Column(JSON, default=dict)
    tool_calls = Column(JSON, default=list)  # list of {tool_name, arguments, result}
    duration_ms = Column(Float, default=0.0)
    token_usage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="traces")


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    strategy_name = Column(String(150), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # EXPEDITED_ALTERNATIVE, BALANCED_TRANSFER_PURCHASE, COST_MINIMALIST
    description = Column(Text, nullable=False)
    total_recovery_cost = Column(Float, nullable=False)
    stockout_risk_score = Column(Float, default=0.0)  # 0.0 - 1.0
    orders_protected = Column(Integer, default=0)
    service_level = Column(Float, default=0.95)  # Expected SLA (0.0 - 1.0)
    actions = Column(JSON, default=list)  # List of proposed actions
    is_recommended = Column(Boolean, default=False)
    status = Column(String(50), default="PROPOSED")  # PROPOSED, APPROVED, REJECTED, EXECUTED
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="recovery_plans")
    action_records = relationship("ActionExecution", back_populates="plan", cascade="all, delete-orphan")


class ActionExecution(Base):
    __tablename__ = "action_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("recovery_plans.id"), nullable=True, index=True)
    action_type = Column(String(100), nullable=False)  # CREATE_PURCHASE_ORDER, TRANSFER_INVENTORY, REALLOCATE_SAFETY_STOCK
    description = Column(Text, nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String(50), default="PENDING_APPROVAL")  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, FAILED
    requires_approval = Column(Boolean, default=True)
    risk_tier = Column(String(50), default="REQUIRES_APPROVAL")  # INFORMATIONAL, LOW_RISK_AUTO, REQUIRES_APPROVAL, RESTRICTED
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="action_executions")
    plan = relationship("RecoveryPlan", back_populates="action_records")
