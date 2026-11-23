export interface Warehouse {
  id: number;
  code: string;
  name: string;
  location: string;
  capacity_units: number;
  current_utilization: number;
  operating_cost_per_day: number;
  created_at: string;
}

export interface Supplier {
  id: number;
  code: string;
  name: string;
  tier: string;
  reliability_score: number;
  avg_lead_time_days: number;
  on_time_delivery_rate: number;
  quality_rating: number;
  contact_email?: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category_id?: number;
  unit_cost: number;
  selling_price: number;
  holding_cost_per_day: number;
  safety_stock: number;
  reorder_point: number;
  min_order_qty: number;
}

export interface InventoryDetail {
  id: number;
  warehouse_id: number;
  warehouse_name: string;
  warehouse_code: string;
  product_id: number;
  product_sku: string;
  product_name: string;
  on_hand_qty: number;
  reserved_qty: number;
  available_qty: number;
  in_transit_qty: number;
  safety_stock: number;
  unit_cost: number;
  total_value: number;
  runway_days: number;
  stockout_risk: 'SAFE' | 'WARNING' | 'CRITICAL';
}

export interface CustomerOrder {
  id: number;
  order_number: string;
  customer_name: string;
  order_date: string;
  required_delivery_date: string;
  status: 'PENDING' | 'AT_RISK' | 'FULFILLED' | 'DELAYED';
  priority: 'STANDARD' | 'EXPEDITED' | 'VIP';
  total_revenue: number;
  line_items: Array<{
    id: number;
    product_id: number;
    product_sku: string;
    product_name: string;
    warehouse_id: number;
    warehouse_name: string;
    ordered_qty: number;
    fulfilled_qty: number;
    unit_price: number;
  }>;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  supplier_id: number;
  supplier_name: string;
  warehouse_id: number;
  warehouse_name: string;
  order_date: string;
  expected_delivery_date: string;
  revised_delivery_date?: string;
  delay_days: number;
  status: string;
  total_cost: number;
  line_items: Array<{
    id: number;
    product_id: number;
    product_sku: string;
    product_name: string;
    qty: number;
    unit_cost: number;
  }>;
}

export interface OperationalIncident {
  id: number;
  incident_key: string;
  incident_type: string;
  title: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'OPEN' | 'INVESTIGATING' | 'MITIGATING' | 'RESOLVED';
  affected_supplier_id?: number;
  affected_supplier_name?: string;
  affected_warehouse_id?: number;
  affected_warehouse_name?: string;
  detected_at: string;
  details_json: Record<string, any>;
}

export interface DashboardOverview {
  total_inventory_value: number;
  total_warehouses: number;
  total_suppliers: number;
  total_products: number;
  active_disruptions: number;
  products_at_risk: number;
  orders_at_risk_count: number;
  revenue_at_risk: number;
  avg_supplier_reliability: number;
  pending_approvals: number;
  recent_incidents: OperationalIncident[];
}

export interface AgentTrace {
  id: number;
  workflow_id: number;
  agent_name: string;
  task: string;
  status: string;
  input_state: Record<string, any>;
  output_state: Record<string, any>;
  tool_calls: Array<{
    tool_name: string;
    arguments: Record<string, any>;
    result: any;
  }>;
  duration_ms: number;
  token_usage: number;
  error_message?: string;
  created_at: string;
}

export interface RecoveryAction {
  action_type: string;
  description: string;
  risk_tier: 'INFORMATIONAL' | 'LOW_RISK_AUTO' | 'REQUIRES_APPROVAL' | 'RESTRICTED';
  requires_approval: boolean;
  payload: Record<string, any>;
}

export interface ActionExecution {
  id: number;
  workflow_id: number;
  plan_id?: number;
  action_type: string;
  description: string;
  payload: Record<string, any>;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'FAILED';
  requires_approval: boolean;
  risk_tier: string;
  approved_by?: string;
  approved_at?: string;
  executed_at?: string;
  result: Record<string, any>;
  created_at: string;
}

export interface RecoveryPlan {
  id: number;
  workflow_id: number;
  strategy_name: string;
  strategy_type: 'EXPEDITED_ALTERNATIVE' | 'BALANCED_TRANSFER_PURCHASE' | 'COST_MINIMALIST';
  description: string;
  total_recovery_cost: number;
  stockout_risk_score: number;
  orders_protected: number;
  service_level: number;
  actions: RecoveryAction[];
  is_recommended: boolean;
  status: string;
  action_records: ActionExecution[];
  created_at: string;
  trade_off_analysis?: {
    advantages: string[];
    disadvantages: string[];
  };
}

export interface Workflow {
  id: number;
  title: string;
  objective: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'REQUIRES_APPROVAL';
  scenario_key?: string;
  started_at: string;
  completed_at?: string;
  total_cost: number;
  summary?: string;
  risk_level: string;
  traces: AgentTrace[];
  recovery_plans: RecoveryPlan[];
  action_executions: ActionExecution[];
}

export interface DecisionPolicy {
  id: number;
  version: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

export interface ExperimentRun {
  id: number;
  policy_id?: number;
  policy_version: string;
  benchmark_suite: string;
  scenarios_evaluated: string[];
  baseline_metrics: {
    policy_version: string;
    avg_recovery_cost: number;
    total_stockout_units: number;
    orders_protected_pct: number;
    avg_lead_time_days: number;
    sla_compliance_rate: number;
  };
  candidate_metrics: {
    policy_version: string;
    avg_recovery_cost: number;
    total_stockout_units: number;
    orders_protected_pct: number;
    avg_lead_time_days: number;
    sla_compliance_rate: number;
  };
  comparison_summary: {
    stockout_reduction_pct: number;
    sla_improvement_pct: number;
    cost_change_pct: number;
    lead_time_reduction_days: number;
    passes_safety_gate: boolean;
    regression_detected: boolean;
    recommendation: string;
  };
  is_promoted: boolean;
  evaluation_notes?: string;
  created_at: string;
}

export interface ObservabilityMetrics {
  total_workflows: number;
  completed_workflows: number;
  failed_workflows: number;
  success_rate_pct: number;
  avg_agent_latency_ms: number;
  total_tokens_consumed: number;
  estimated_llm_cost_usd: number;
  total_tools_invoked: number;
  agent_performance_breakdown: Array<{
    agent_name: string;
    execution_count: number;
    avg_latency_ms: number;
    total_tokens: number;
    tool_calls_count: number;
    failures: number;
  }>;
}

export interface Scenario {
  key: string;
  name: string;
  description: string;
  difficulty: string;
  recommended_objective: string;
}
