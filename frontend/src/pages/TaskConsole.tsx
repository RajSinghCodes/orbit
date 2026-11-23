import React, { useState, useEffect } from 'react';
import {
  Sparkles, Play, ShieldAlert, CheckCircle2, Clock,
  ArrowRight, RefreshCw, Layers, Check, AlertCircle
} from 'lucide-react';
import { Scenario, Workflow } from '../types';
import { api } from '../services/api';

interface Props {
  onNavigate: (tab: string) => void;
  onWorkflowSelected: (workflow: Workflow) => void;
  activeWorkflow: Workflow | null;
}

export const TaskConsole: React.FC<Props> = ({ onNavigate, onWorkflowSelected, activeWorkflow }) => {
  const [objective, setObjective] = useState(
    "Investigate the supplier disruption, identify all affected products and customer orders, estimate the business impact, and prepare the best recovery strategy while minimizing additional costs."
  );
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioKey, setSelectedScenarioKey] = useState<string>("SUPPLIER_DELAY_APEX");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<string>("");
  const [latestWorkflow, setLatestWorkflow] = useState<Workflow | null>(activeWorkflow);

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const scs = await api.getScenarios();
      setScenarios(scs);
    } catch (err) {
      console.error('Failed to load scenarios:', err);
    }
  };

  const handleSelectScenario = (sc: Scenario) => {
    setSelectedScenarioKey(sc.key);
    setObjective(sc.recommended_objective);
  };

  const handleRunInvestigation = async () => {
    if (!objective.trim()) return;

    setIsExecuting(true);
    setExecutionMessage("Initializing LangGraph multi-agent orchestrator...");

    try {
      // First ensure scenario condition is active if applicable
      if (selectedScenarioKey) {
        await api.triggerScenario(selectedScenarioKey);
      }

      setExecutionMessage("Dispatching Supervisor, Detection, Impact, and Forecasting agents...");
      const wf = await api.createWorkflow(objective, selectedScenarioKey);
      
      setLatestWorkflow(wf);
      onWorkflowSelected(wf);
      setExecutionMessage("Workflow complete! Optimal recovery strategies generated.");
    } catch (err: any) {
      console.error('Workflow execution failed:', err);
      setExecutionMessage(`Execution Error: ${err.message || 'Failed'}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-950/60 to-indigo-950/40 border border-blue-900/40 rounded-2xl p-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 bg-blue-500/20 text-blue-400 rounded-xl">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">ORBIT Autonomous Operational Task Console</h2>
            <p className="text-xs text-blue-300/80">
              State-machine coordinated multi-agent intelligence. State your objective in natural language or choose a benchmark scenario.
            </p>
          </div>
        </div>
      </div>

      {/* Preset Scenarios Selector */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Preset Operational Benchmark Scenarios</span>
          <span>Click to Auto-Configure Objective</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioKey === sc.key;
            return (
              <button
                key={sc.key}
                onClick={() => handleSelectScenario(sc)}
                className={`text-left p-3.5 rounded-xl border transition-all text-xs flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-950/40 border-blue-500 text-blue-200 shadow-md shadow-blue-500/10'
                    : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-200">{sc.name.split(':')[0]}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      sc.difficulty === 'Critical' ? 'bg-rose-500/20 text-rose-400' :
                      sc.difficulty === 'High' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {sc.difficulty}
                    </span>
                  </div>
                  <p className="text-slate-400 line-clamp-2">{sc.description}</p>
                </div>
                {isSelected && (
                  <div className="mt-2.5 flex items-center text-blue-400 font-medium">
                    <Check className="w-3.5 h-3.5 mr-1" /> Selected Scenario
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Natural Language Objective Input */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Operational Objective
          </label>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            rows={3}
            placeholder="Describe operational objective (e.g., Investigate supplier disruption, evaluate stockout risks, and optimize recovery)..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors resize-none"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center text-xs text-slate-400 space-x-4">
            <span className="flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mr-1" />
              LangGraph Orchestration
            </span>
            <span className="flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mr-1" />
              Grounded Numerical Math
            </span>
            <span className="flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mr-1" />
              Human-in-the-Loop Safety
            </span>
          </div>

          <button
            onClick={handleRunInvestigation}
            disabled={isExecuting || !objective.trim()}
            className="flex items-center space-x-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium rounded-xl text-sm transition-all shadow-lg shadow-blue-600/25 cursor-pointer"
          >
            {isExecuting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Coordinating Agents...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Execute Autonomous Investigation</span>
              </>
            )}
          </button>
        </div>

        {/* Execution Status Bar */}
        {isExecuting && (
          <div className="bg-blue-950/40 border border-blue-800/40 rounded-xl p-3 flex items-center space-x-3 text-xs text-blue-300">
            <Clock className="w-4 h-4 text-blue-400 animate-spin" />
            <span>{executionMessage}</span>
          </div>
        )}
      </div>

      {/* Investigation Results Presentation */}
      {latestWorkflow && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div>
              <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">
                Workflow #{latestWorkflow.id} · Status: {latestWorkflow.status}
              </span>
              <h3 className="text-lg font-bold text-slate-100 mt-1">{latestWorkflow.title}</h3>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onNavigate('live-agents')}
                className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
              >
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                <span>View Live Execution Graph</span>
              </button>
              <button
                onClick={() => onNavigate('recovery-plans')}
                className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
              >
                <span>Review & Approve Recovery Plans</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="bg-slate-950/70 rounded-xl p-4 border border-slate-800/60">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Executive Summary</h4>
            <p className="text-sm text-slate-300 leading-relaxed">{latestWorkflow.summary}</p>
          </div>

          {/* 3 Generated Recovery Plans Preview */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Generated Recovery Strategies ({latestWorkflow.recovery_plans?.length || 0} Options Evaluated)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {latestWorkflow.recovery_plans?.map((plan) => (
                <div
                  key={plan.id}
                  className={`p-4 rounded-xl border flex flex-col justify-between ${
                    plan.is_recommended
                      ? 'bg-blue-950/30 border-blue-500/60 shadow-lg shadow-blue-500/10'
                      : 'bg-slate-950/60 border-slate-800'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-slate-200">{plan.strategy_name}</span>
                      {plan.is_recommended && (
                        <span className="text-[10px] bg-blue-500 text-slate-950 font-bold px-1.5 py-0.5 rounded">
                          RECOMMENDED
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-3 mb-3">{plan.description}</p>
                  </div>

                  <div className="space-y-1.5 text-xs border-t border-slate-800/80 pt-3">
                    <div className="flex justify-between text-slate-400">
                      <span>Total Recovery Cost:</span>
                      <span className="font-semibold text-slate-200">${plan.total_recovery_cost.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Stockout Risk:</span>
                      <span className={`font-semibold ${plan.stockout_risk_score > 0.15 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {Math.round(plan.stockout_risk_score * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Expected Service Level:</span>
                      <span className="font-semibold text-emerald-400">
                        {Math.round(plan.service_level * 100)}% SLA
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Orders Protected:</span>
                      <span className="font-semibold text-slate-200">{plan.orders_protected} Orders</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
