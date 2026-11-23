from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session
from app.agents.state import OrbitWorkflowState
from app.agents.supervisor import SupervisorAgent
from app.agents.detection import DetectionAgent
from app.agents.impact_analysis import ImpactAnalysisAgent
from app.agents.demand_forecast import DemandForecastingAgent
from app.agents.supplier_intel import SupplierIntelligenceAgent
from app.agents.optimization import OptimizationAgent
from app.agents.verification import VerificationAgent

def build_orbit_workflow_graph(db: Session):
    """
    Constructs the compiled LangGraph multi-agent state graph for ORBIT.
    Defines explicit agent nodes, directed workflow edges, and typed state transitions.
    """
    workflow_graph = StateGraph(OrbitWorkflowState)

    # Node wrappers injecting database session
    def supervisor_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = SupervisorAgent.execute(state, db)
        return {**state, **updates}

    def detection_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = DetectionAgent.execute(state, db)
        return {**state, **updates}

    def impact_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = ImpactAnalysisAgent.execute(state, db)
        return {**state, **updates}

    def forecast_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = DemandForecastingAgent.execute(state, db)
        return {**state, **updates}

    def supplier_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = SupplierIntelligenceAgent.execute(state, db)
        return {**state, **updates}

    def optimization_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = OptimizationAgent.execute(state, db)
        return {**state, **updates}

    def verification_node(state: OrbitWorkflowState) -> OrbitWorkflowState:
        updates = VerificationAgent.execute(state, db)
        return {**state, **updates}

    # Register agent nodes
    workflow_graph.add_node("supervisor", supervisor_node)
    workflow_graph.add_node("detection", detection_node)
    workflow_graph.add_node("impact_analysis", impact_node)
    workflow_graph.add_node("demand_forecast", forecast_node)
    workflow_graph.add_node("supplier_intel", supplier_node)
    workflow_graph.add_node("optimization", optimization_node)
    workflow_graph.add_node("verification", verification_node)

    # Define sequential dependency DAG
    workflow_graph.add_edge(START, "supervisor")
    workflow_graph.add_edge("supervisor", "detection")
    workflow_graph.add_edge("detection", "impact_analysis")
    workflow_graph.add_edge("impact_analysis", "demand_forecast")
    workflow_graph.add_edge("demand_forecast", "supplier_intel")
    workflow_graph.add_edge("supplier_intel", "optimization")
    workflow_graph.add_edge("optimization", "verification")
    workflow_graph.add_edge("verification", END)

    return workflow_graph.compile()
