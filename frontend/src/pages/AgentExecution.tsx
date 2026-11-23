import React, { useState, useEffect } from 'react';
import {
  Workflow as WorkflowIcon, CheckCircle2, Clock, Terminal,
  Cpu, ArrowDown, ChevronRight, AlertCircle, Wrench, RefreshCw
} from 'lucide-react';
import { Workflow, AgentTrace } from '../types';
import { api } from '../services/api';

interface Props {
  activeWorkflow: Workflow | null;
  onRefreshWorkflow?: () => void;
}

export const AgentExecution: React.FC<Props> = ({ activeWorkflow }) => {
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<AgentTrace | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeWorkflow?.id) {
      loadTraces(activeWorkflow.id);
    }
  }, [activeWorkflow]);

  const loadTraces = async (wfId: number) => {
    setLoading(true);
    try {
      const data = await api.getWorkflowTraces(wfId);
      setTraces(data);
      if (data.length > 0) {
        setSelectedTrace(data[0]);
      }
    } catch (err) {
      console.error('Failed to load traces:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!activeWorkflow) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-12 text-center max-w-xl mx-auto space-y-4">
        <Cpu className="w-12 h-12 text-slate-600 mx-auto" />
        <h3 className="text-lg font-semibold text-slate-300">No Active Workflow Selected</h3>
        <p className="text-xs text-slate-500">
          Launch an operational investigation from the ORBIT Task Console to visualize live multi-agent execution traces.
        </p>
      </div>
    );
  }

  const agentOrder = [
    "Supervisor Agent",
    "Detection Agent",
    "Impact Analysis Agent",
    "Demand Forecasting Agent",
    "Supplier Intelligence Agent",
    "Optimization Agent",
    "Verification Agent"
  ];

  return (
    <div className="space-y-6">
      {/* Workflow Execution Header */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 mb-1">
            <span>Workflow #{activeWorkflow.id}</span>
            <span>·</span>
            <span>DAG Status: {activeWorkflow.status}</span>
          </div>
          <h2 className="text-lg font-bold text-slate-100">{activeWorkflow.title}</h2>
        </div>
        <button
          onClick={() => activeWorkflow?.id && loadTraces(activeWorkflow.id)}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Traces</span>
        </button>
      </div>

      {/* Main Grid: Multi-Agent DAG Column on left, Selected Agent Inspector on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Agent Graph Pipeline (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            LangGraph Execution Pipeline ({traces.length} Traces Logged)
          </div>

          <div className="space-y-3 relative">
            {traces.map((trace, idx) => {
              const isSelected = selectedTrace?.id === trace.id;
              const hasTools = trace.tool_calls && trace.tool_calls.length > 0;

              return (
                <div key={trace.id} className="relative">
                  {idx < traces.length - 1 && (
                    <div className="absolute left-6 top-12 bottom-[-16px] w-0.5 bg-slate-800 -z-0" />
                  )}

                  <div
                    onClick={() => setSelectedTrace(trace)}
                    className={`relative z-10 p-4 rounded-xl border transition-all cursor-pointer flex items-start space-x-3 ${
                      isSelected
                        ? 'bg-blue-950/40 border-blue-500 shadow-md shadow-blue-500/10'
                        : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400 mt-0.5">
                      <Cpu className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">{trace.agent_name}</span>
                        <span className="text-[10px] font-mono text-slate-400">{Math.round(trace.duration_ms)} ms</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-1">{trace.task}</p>

                      <div className="flex items-center space-x-3 mt-2 text-[10px] text-slate-500">
                        <span className="flex items-center text-emerald-400">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Completed
                        </span>
                        {hasTools && (
                          <span className="flex items-center text-indigo-400">
                            <Wrench className="w-3 h-3 mr-1" /> {trace.tool_calls.length} Tools Invoked
                          </span>
                        )}
                        <span>{trace.token_usage} tokens</span>
                      </div>
                    </div>

                    <ChevronRight className={`w-4 h-4 text-slate-500 mt-1 transition-transform ${isSelected ? 'rotate-90 text-blue-400' : ''}`} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Deep-Dive Agent Trace Inspector (7 cols) */}
        <div className="lg:col-span-7">
          {selectedTrace ? (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">Agent Trace Inspector</span>
                  <h3 className="text-lg font-bold text-slate-100 mt-0.5">{selectedTrace.agent_name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{selectedTrace.task}</p>
                </div>
                <div className="text-right text-xs">
                  <div className="text-slate-200 font-mono font-bold">{Math.round(selectedTrace.duration_ms)} ms</div>
                  <div className="text-slate-500">{selectedTrace.token_usage} Tokens Used</div>
                </div>
              </div>

              {/* Tool Calls Breakdown */}
              {selectedTrace.tool_calls && selectedTrace.tool_calls.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    <Wrench className="w-4 h-4 text-indigo-400" />
                    <span>Deterministic Tool Invocations ({selectedTrace.tool_calls.length})</span>
                  </div>

                  <div className="space-y-2">
                    {selectedTrace.tool_calls.map((tool, tIdx) => (
                      <div key={tIdx} className="bg-slate-950 rounded-xl p-3 border border-slate-800/80 font-mono text-xs">
                        <div className="flex items-center justify-between text-indigo-400 font-bold mb-1.5">
                          <span>$ tool_call: {tool.tool_name}()</span>
                          <span className="text-[10px] text-slate-500 font-normal">Executed</span>
                        </div>
                        <div className="text-slate-400 text-[11px] mb-1">
                          <span className="text-slate-500">Args: </span>
                          {JSON.stringify(tool.arguments)}
                        </div>
                        <div className="text-emerald-400 text-[11px] bg-slate-900/80 p-2 rounded border border-slate-800/50 overflow-x-auto">
                          <span className="text-slate-500">Output: </span>
                          {JSON.stringify(tool.result, null, 2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* State I/O */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Input State */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent Input State</div>
                  <pre className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 max-h-56 overflow-y-auto">
                    {JSON.stringify(selectedTrace.input_state, null, 2)}
                  </pre>
                </div>

                {/* Output State */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent Output State</div>
                  <pre className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] font-mono text-emerald-300 max-h-56 overflow-y-auto">
                    {JSON.stringify(selectedTrace.output_state, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-xs">
              Select an agent from the pipeline to inspect inputs, outputs, and tool calls.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
