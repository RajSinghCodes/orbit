import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, CheckCircle2, XCircle, Play, Check,
  AlertTriangle, DollarSign, Truck, Package, Clock, RefreshCw
} from 'lucide-react';
import { Workflow, RecoveryPlan, ActionExecution } from '../types';
import { api } from '../services/api';

interface Props {
  activeWorkflow: Workflow | null;
  onRefreshWorkflow?: () => void;
}

export const RecoveryPlanApprovals: React.FC<Props> = ({ activeWorkflow, onRefreshWorkflow }) => {
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [plans, setPlans] = useState<RecoveryPlan[]>([]);
  const [executing, setExecuting] = useState(false);
  const [executionMessage, setExecutionMessage] = useState<string>('');

  useEffect(() => {
    if (activeWorkflow?.id) {
      loadPlans(activeWorkflow.id);
    }
  }, [activeWorkflow]);

  const loadPlans = async (wfId: number) => {
    try {
      const data = await api.getWorkflowPlans(wfId);
      setPlans(data);
      if (data.length > 0) {
        const rec = data.find(p => p.is_recommended) || data[0];
        setSelectedPlanId(rec.id);
      }
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  };

  const selectedPlan = plans.find(p => p.id === selectedPlanId);

  const handleApproveAction = async (actionId: number, approve: boolean) => {
    if (!activeWorkflow?.id) return;
    try {
      await api.approveAction(activeWorkflow.id, actionId, approve, 'Operations Lead');
      await loadPlans(activeWorkflow.id);
      if (onRefreshWorkflow) onRefreshWorkflow();
    } catch (err) {
      console.error('Failed to update action status:', err);
    }
  };

  const handleExecuteAllApproved = async () => {
    if (!activeWorkflow?.id) return;
    setExecuting(true);
    setExecutionMessage('Issuing simulated ERP purchase orders and scheduling WMS transfer orders...');

    try {
      const res = await api.executeApprovedActions(activeWorkflow.id);
      setExecutionMessage(`Successfully executed ${res.executed_count} authorized operations.`);
      await loadPlans(activeWorkflow.id);
      if (onRefreshWorkflow) onRefreshWorkflow();
    } catch (err: any) {
      setExecutionMessage(`Execution Error: ${err.message || 'Failed'}`);
    } finally {
      setExecuting(false);
    }
  };

  if (!activeWorkflow) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-12 text-center max-w-xl mx-auto space-y-4">
        <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto" />
        <h3 className="text-lg font-semibold text-slate-300">No Recovery Plan Available</h3>
        <p className="text-xs text-slate-500">
          Run an investigation from the Task Console to generate and compare competing recovery plans.
        </p>
      </div>
    );
  }

  const allActions = selectedPlan?.action_records || [];
  const pendingCount = allActions.filter(a => a.status === 'PENDING_APPROVAL').length;
  const approvedCount = allActions.filter(a => a.status === 'APPROVED').length;
  const executedCount = allActions.filter(a => a.status === 'EXECUTED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">
            Decision Intelligence & Human Oversight
          </span>
          <h2 className="text-xl font-bold text-slate-100">Recovery Strategy Comparison & Action Approvals</h2>
        </div>

        <div className="flex items-center space-x-2">
          {approvedCount > 0 && executedCount < allActions.length && (
            <button
              onClick={handleExecuteAllApproved}
              disabled={executing}
              className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-medium transition-all shadow-md shadow-emerald-600/20 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Execute {approvedCount} Approved Actions</span>
            </button>
          )}
        </div>
      </div>

      {executionMessage && (
        <div className="bg-emerald-950/40 border border-emerald-800/40 rounded-xl p-3 text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{executionMessage}</span>
        </div>
      )}

      {/* Side-by-Side 3 Recovery Strategies Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plans.map((p) => {
          const isSelected = p.id === selectedPlanId;
          return (
            <div
              key={p.id}
              onClick={() => setSelectedPlanId(p.id)}
              className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-blue-950/30 border-blue-500 shadow-xl shadow-blue-500/10'
                  : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-200">{p.strategy_name}</span>
                  {p.is_recommended && (
                    <span className="text-[10px] bg-blue-500 text-slate-950 font-bold px-2 py-0.5 rounded-full">
                      OPTIMAL
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mb-4 line-clamp-3 leading-relaxed">{p.description}</p>
              </div>

              {/* Metrics Pill Grid */}
              <div className="space-y-2 text-xs border-t border-slate-800/80 pt-3 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Total Recovery Cost:</span>
                  <span className="font-bold text-slate-100">${p.total_recovery_cost.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Stockout Risk:</span>
                  <span className={`font-bold ${p.stockout_risk_score > 0.15 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {Math.round(p.stockout_risk_score * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Expected SLA:</span>
                  <span className="font-bold text-emerald-400">{Math.round(p.service_level * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-sans">Protected Orders:</span>
                  <span className="font-bold text-slate-200">{p.orders_protected} Orders</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                <span className="text-slate-500">{p.actions?.length || 0} Actions</span>
                <span className={`font-medium ${isSelected ? 'text-blue-400' : 'text-slate-400'}`}>
                  {isSelected ? '✓ Plan Selected' : 'Select Strategy'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Action Approvals for Selected Strategy */}
      {selectedPlan && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-xs font-mono text-blue-400 uppercase tracking-wider">Action Plan Authorization</span>
              <h3 className="text-lg font-bold text-slate-100 mt-0.5">{selectedPlan.strategy_name}</h3>
              <p className="text-xs text-slate-400">
                All external commitments, purchase orders, and warehouse transfers require explicit human approval.
              </p>
            </div>
            <div className="text-right text-xs">
              <span className="text-slate-400">Pending Approvals: </span>
              <span className="font-bold text-amber-400">{pendingCount}</span>
            </div>
          </div>

          {/* Action Execution Items List */}
          <div className="space-y-3">
            {allActions.map((act) => {
              const payload = act.payload || {};
              const isApproved = act.status === 'APPROVED';
              const isExecuted = act.status === 'EXECUTED';
              const isPending = act.status === 'PENDING_APPROVAL';

              return (
                <div key={act.id} className="bg-slate-950 rounded-xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-blue-400">{act.action_type}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        isExecuted ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        isApproved ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {act.status}
                      </span>
                      <span className="text-[10px] text-slate-500 font-sans">
                        Tier: {act.risk_tier}
                      </span>
                    </div>
                    <div className="text-xs text-slate-200">{act.description}</div>
                    <div className="text-[11px] font-mono text-slate-400">
                      Payload: {JSON.stringify(payload)}
                    </div>
                    {isExecuted && act.result && (
                      <div className="text-[11px] font-mono text-emerald-400 bg-emerald-950/20 p-1.5 rounded border border-emerald-900/30">
                        Receipt: {JSON.stringify(act.result)}
                      </div>
                    )}
                  </div>

                  {/* Approve / Reject Controls */}
                  <div className="flex items-center space-x-2 self-end sm:self-center shrink-0">
                    {isPending && (
                      <>
                        <button
                          onClick={() => handleApproveAction(act.id, true)}
                          className="flex items-center space-x-1 px-3 py-1.5 bg-emerald-600/30 hover:bg-emerald-600 text-emerald-300 hover:text-white rounded-lg text-xs font-medium transition-colors"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => handleApproveAction(act.id, false)}
                          className="flex items-center space-x-1 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white rounded-lg text-xs font-medium transition-colors"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </>
                    )}
                    {isApproved && (
                      <span className="text-xs text-blue-400 flex items-center font-medium">
                        <CheckCircle2 className="w-4 h-4 mr-1" /> Approved by {act.approved_by || 'Reviewer'}
                      </span>
                    )}
                    {isExecuted && (
                      <span className="text-xs text-emerald-400 flex items-center font-medium">
                        <CheckCircle2 className="w-4 h-4 mr-1" /> Simulated Execution Complete
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
