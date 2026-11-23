import {
  DashboardOverview, Warehouse, Supplier, Product, InventoryDetail,
  CustomerOrder, PurchaseOrder, OperationalIncident, Scenario,
  Workflow, AgentTrace, RecoveryPlan, DecisionPolicy,
  ExperimentRun, ObservabilityMetrics
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    },
    ...options
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorBody}`);
  }
  return res.json();
}

export const api = {
  // Health
  checkHealth: () => fetchJson<{ status: string; platform: string; version: string; llm_mode: string }>('/health'),

  // Dashboard
  getDashboard: () => fetchJson<DashboardOverview>('/dashboard'),

  // Supply Chain
  getWarehouses: () => fetchJson<Warehouse[]>('/supply-chain/warehouses'),
  getSuppliers: () => fetchJson<Supplier[]>('/supply-chain/suppliers'),
  getProducts: () => fetchJson<Product[]>('/supply-chain/products'),
  getInventory: (warehouseId?: number) =>
    fetchJson<InventoryDetail[]>(`/supply-chain/inventory${warehouseId ? `?warehouse_id=${warehouseId}` : ''}`),
  getCustomerOrders: (status?: string) =>
    fetchJson<CustomerOrder[]>(`/supply-chain/customer-orders${status ? `?status=${status}` : ''}`),
  getPurchaseOrders: () => fetchJson<PurchaseOrder[]>('/supply-chain/purchase-orders'),
  getDemandHistory: (productId: number = 1, warehouseId: number = 1) =>
    fetchJson<Array<{ date: string; demand_qty: number }>>(`/supply-chain/demand-history?product_id=${productId}&warehouse_id=${warehouseId}`),

  // Incidents
  getIncidents: () => fetchJson<OperationalIncident[]>('/incidents'),
  getIncident: (id: number) => fetchJson<OperationalIncident>(`/incidents/${id}`),

  // Scenarios
  getScenarios: () => fetchJson<Scenario[]>('/scenarios'),
  triggerScenario: (key: string) =>
    fetchJson<{ scenario: string; status: string; message: string; recommended_objective: string }>(`/scenarios/${key}/trigger`, {
      method: 'POST'
    }),

  // Workflows
  listWorkflows: () => fetchJson<Workflow[]>('/workflows'),
  createWorkflow: (objective: string, scenarioKey?: string) =>
    fetchJson<Workflow>('/workflows', {
      method: 'POST',
      body: JSON.stringify({ objective, scenario_key: scenarioKey })
    }),
  getWorkflow: (id: number) => fetchJson<Workflow>(`/workflows/${id}`),
  getWorkflowTraces: (id: number) => fetchJson<AgentTrace[]>(`/workflows/${id}/traces`),
  getWorkflowPlans: (id: number) => fetchJson<RecoveryPlan[]>(`/workflows/${id}/plans`),
  approveAction: (workflowId: number, actionId: number, approved: boolean, reviewerName: string = 'Operations Lead') =>
    fetchJson<{ action_id: number; status: string; approved_by?: string }>(`/workflows/${workflowId}/actions/${actionId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ action_id: actionId, approved, reviewer_name: reviewerName })
    }),
  executeApprovedActions: (workflowId: number) =>
    fetchJson<{ workflow_id: number; executed_count: number; message: string }>(`/workflows/${workflowId}/execute-approved`, {
      method: 'POST'
    }),

  // Self-Improvement
  getPolicies: () => fetchJson<DecisionPolicy[]>('/improvement/policies'),
  getExperiments: () => fetchJson<ExperimentRun[]>('/improvement/experiments'),
  runExperiment: (candidateVersion: string, candidateParams: Record<string, any>) =>
    fetchJson<ExperimentRun>('/improvement/run-experiment', {
      method: 'POST',
      body: JSON.stringify({
        candidate_version: candidateVersion,
        candidate_parameters: candidateParams,
        benchmark_suite: 'STANDARD_SUPPLY_CHAIN_BENCHMARK'
      })
    }),
  promotePolicy: (experimentId: number, approvedBy: string = 'Operations Lead') =>
    fetchJson<{ promoted_version: string; status: string; activated_at: string }>('/improvement/promote', {
      method: 'POST',
      body: JSON.stringify({ experiment_id: experimentId, approved_by: approvedBy })
    }),
  rollbackPolicy: (targetVersion: string = 'v1.0.0-baseline') =>
    fetchJson<{ active_version: string; status: string; message: string }>(`/improvement/rollback?target_version=${targetVersion}`, {
      method: 'POST'
    }),

  // Observability
  getObservabilityMetrics: () => fetchJson<ObservabilityMetrics>('/observability/metrics')
};
