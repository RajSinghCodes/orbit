import React, { useState, useEffect } from 'react';
import {
  Activity, Cpu, DollarSign, Clock, CheckCircle2,
  AlertTriangle, Wrench, RefreshCw, BarChart2
} from 'lucide-react';
import { ObservabilityMetrics, Workflow, AgentTrace } from '../types';
import { api } from '../services/api';

export const ObservabilityTraces: React.FC = () => {
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null);
  const [workflowTraces, setWorkflowTraces] = useState<AgentTrace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadObservability();
  }, []);

  const loadObservability = async () => {
    setLoading(true);
    try {
      const [m, wfs] = await Promise.all([
        api.getObservabilityMetrics(),
        api.listWorkflows()
      ]);
      setMetrics(m);
      setWorkflows(wfs);
      if (wfs.length > 0) {
        setSelectedWorkflowId(wfs[0].id);
        const trs = await api.getWorkflowTraces(wfs[0].id);
        setWorkflowTraces(trs);
      }
    } catch (err) {
      console.error('Failed to load observability data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWorkflow = async (id: number) => {
    setSelectedWorkflowId(id);
    try {
      const trs = await api.getWorkflowTraces(id);
      setWorkflowTraces(trs);
    } catch (err) {
      console.error('Failed to load traces:', err);
    }
  };

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Clock className="w-6 h-6 animate-spin mr-2" />
        Loading System Observability & Traces...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Multi-Agent Observability & Runtime Telemetry</h2>
          <p className="text-xs text-slate-400">
            Real-time audit traces, execution latencies, token consumption, and deterministic tool invocations
          </p>
        </div>
        <button
          onClick={loadObservability}
          className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase mb-1">
            <span>Workflow Completion Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">{metrics.success_rate_pct}%</div>
          <div className="text-xs text-slate-400 mt-1">{metrics.completed_workflows} of {metrics.total_workflows} Workflows</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase mb-1">
            <span>Average Agent Latency</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-blue-400">{metrics.avg_agent_latency_ms} ms</div>
          <div className="text-xs text-slate-400 mt-1">Per agent task invocation</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase mb-1">
            <span>Token Consumption & Cost</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">{metrics.total_tokens_consumed.toLocaleString()}</div>
          <div className="text-xs text-emerald-400 mt-1">${metrics.estimated_llm_cost_usd} estimated LLM spend</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs uppercase mb-1">
            <span>Tools Dispatched</span>
            <Wrench className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-indigo-400">{metrics.total_tools_invoked} Calls</div>
          <div className="text-xs text-slate-400 mt-1">Deterministic calculations</div>
        </div>
      </div>

      {/* Agent Performance Breakdown Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Specialized Agent Performance Breakdown
          </h3>
        </div>
        <table className="w-full text-left text-xs text-slate-300 font-mono">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-sans">
            <tr>
              <th className="py-3 px-4">Agent Role</th>
              <th className="py-3 px-4 text-right">Invocations</th>
              <th className="py-3 px-4 text-right">Avg Duration</th>
              <th className="py-3 px-4 text-right">Tokens Consumed</th>
              <th className="py-3 px-4 text-right">Tool Invocations</th>
              <th className="py-3 px-4 text-center">Failures</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {metrics.agent_performance_breakdown.map((ag) => (
              <tr key={ag.agent_name} className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">{ag.agent_name}</td>
                <td className="py-3 px-4 text-right">{ag.execution_count}</td>
                <td className="py-3 px-4 text-right text-blue-400">{ag.avg_latency_ms} ms</td>
                <td className="py-3 px-4 text-right text-slate-400">{ag.total_tokens}</td>
                <td className="py-3 px-4 text-right text-indigo-400 font-bold">{ag.tool_calls_count}</td>
                <td className="py-3 px-4 text-center">
                  {ag.failures > 0 ? (
                    <span className="text-rose-400 font-bold">{ag.failures}</span>
                  ) : (
                    <span className="text-emerald-400">0</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Historical Workflow Trace Browser */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historical Workflows</div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {workflows.map((wf) => (
              <button
                key={wf.id}
                onClick={() => handleSelectWorkflow(wf.id)}
                className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                  selectedWorkflowId === wf.id
                    ? 'bg-blue-950/40 border-blue-500 text-blue-200'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="font-mono text-[10px] text-blue-400">Workflow #{wf.id}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{wf.status}</span>
                </div>
                <div className="font-medium text-slate-200 truncate">{wf.title}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-8 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Trace Sequence for Workflow #{selectedWorkflowId}
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {workflowTraces.map((tr) => (
              <div key={tr.id} className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 text-xs font-mono">
                <div className="flex justify-between items-center text-slate-200 font-bold mb-1">
                  <span className="text-blue-400">{tr.agent_name}</span>
                  <span className="text-slate-500 text-[10px]">{Math.round(tr.duration_ms)} ms · {tr.token_usage} tokens</span>
                </div>
                <div className="text-slate-400 font-sans text-xs mb-2">{tr.task}</div>
                {tr.tool_calls?.map((tc, idx) => (
                  <div key={idx} className="text-indigo-400 text-[11px] bg-slate-900/60 p-1.5 rounded mb-1">
                    ↳ tool: {tc.tool_name}()
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
