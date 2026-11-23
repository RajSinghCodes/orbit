import React, { useState, useEffect } from 'react';
import {
  FlaskConical, CheckCircle2, XCircle, TrendingDown, TrendingUp,
  Sliders, ArrowRight, RotateCcw, AlertTriangle, ShieldCheck, RefreshCw, Check
} from 'lucide-react';
import { DecisionPolicy, ExperimentRun } from '../types';
import { api } from '../services/api';

export const SelfImprovementLab: React.FC = () => {
  const [policies, setPolicies] = useState<DecisionPolicy[]>([]);
  const [experiments, setExperiments] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningExperiment, setRunningExperiment] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string>('');

  // Editable candidate parameters
  const [candVersion, setCandVersion] = useState('v1.2.0-dynamic-reliability');
  const [candRelWeight, setCandRelWeight] = useState(0.45);
  const [candLeadWeight, setCandLeadWeight] = useState(0.35);
  const [candPriceWeight, setCandPriceWeight] = useState(0.20);
  const [candSafetyRatio, setCandSafetyRatio] = useState(1.30);

  useEffect(() => {
    loadLabData();
  }, []);

  const loadLabData = async () => {
    setLoading(true);
    try {
      const [pols, exps] = await Promise.all([
        api.getPolicies(),
        api.getExperiments()
      ]);
      setPolicies(pols);
      setExperiments(exps);
    } catch (err) {
      console.error('Failed to load self-improvement data:', err);
    } finally {
      setLoading(false);
    }
  };

  const activePolicy = policies.find(p => p.is_active) || policies[0];
  const latestExperiment = experiments[0];

  const handleRunExperiment = async () => {
    setRunningExperiment(true);
    setFeedbackMessage('Evaluating candidate policy against 3 benchmark holdout scenarios...');
    try {
      const exp = await api.runExperiment(candVersion, {
        supplier_reliability_weight: candRelWeight,
        lead_time_weight: candLeadWeight,
        unit_price_weight: candPriceWeight,
        min_supplier_reliability_threshold: 0.90,
        safety_stock_buffer_ratio: candSafetyRatio
      });
      setFeedbackMessage(`Experiment Complete: Stockout rate reduced by ${exp.comparison_summary.stockout_reduction_pct}%. Safety gate: ${exp.comparison_summary.passes_safety_gate ? 'PASSED' : 'REJECTED'}.`);
      await loadLabData();
    } catch (err: any) {
      setFeedbackMessage(`Experiment failed: ${err.message || 'Error'}`);
    } finally {
      setRunningExperiment(false);
    }
  };

  const handlePromote = async (expId: number) => {
    try {
      const res = await api.promotePolicy(expId, 'VP of Supply Chain Operations');
      setFeedbackMessage(`Successfully promoted ${res.promoted_version} to active production.`);
      await loadLabData();
    } catch (err: any) {
      setFeedbackMessage(`Promotion failed: ${err.message}`);
    }
  };

  const handleRollback = async () => {
    try {
      const res = await api.rollbackPolicy('v1.0.0-baseline');
      setFeedbackMessage(res.message);
      await loadLabData();
    } catch (err: any) {
      setFeedbackMessage(`Rollback failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-950/60 to-indigo-950/40 border border-purple-900/40 rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 text-purple-400 rounded-xl">
              <FlaskConical className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Self-Improvement & Policy Experimentation Laboratory</h2>
              <p className="text-xs text-purple-300/80">
                Empirical policy optimization. Compare decision policies against controlled holdout benchmark suites without hallucinations.
              </p>
            </div>
          </div>

          <button
            onClick={handleRollback}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
            <span>Rollback to Baseline</span>
          </button>
        </div>
      </div>

      {feedbackMessage && (
        <div className="bg-purple-950/40 border border-purple-800/40 rounded-xl p-3 text-xs text-purple-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-purple-400" />
          <span>{feedbackMessage}</span>
        </div>
      )}

      {/* Policy Comparison Panel: Active Baseline vs Candidate Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Baseline Policy Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full font-bold">
                ACTIVE PRODUCTION POLICY
              </span>
              <h3 className="text-base font-bold text-slate-100 mt-2">{activePolicy?.name || 'Cost-Prioritizing Baseline'}</h3>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">{activePolicy?.version || 'v1.0.0-baseline'}</p>
            </div>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="flex justify-between items-center text-slate-300">
              <span className="font-sans text-slate-400">Supplier Reliability Weight (W_rel):</span>
              <span className="font-bold text-slate-200">{activePolicy?.parameters?.supplier_reliability_weight ?? 0.25}</span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="font-sans text-slate-400">Lead Time Weight (W_lead):</span>
              <span className="font-bold text-slate-200">{activePolicy?.parameters?.lead_time_weight ?? 0.35}</span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="font-sans text-slate-400">Unit Price Weight (W_price):</span>
              <span className="font-bold text-slate-200">{activePolicy?.parameters?.unit_price_weight ?? 0.40}</span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span className="font-sans text-slate-400">Safety Stock Buffer Ratio:</span>
              <span className="font-bold text-slate-200">{activePolicy?.parameters?.safety_stock_buffer_ratio ?? 1.15}x</span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            Diagnosis: Overweighting unit price causes procurement to favor slow Tier-2 suppliers (10-12 day lead times), triggering stockout cliffs during unexpected disruption.
          </div>
        </div>

        {/* Candidate Policy Formulation Card */}
        <div className="bg-slate-900/80 border border-purple-500/40 rounded-2xl p-6 space-y-4 shadow-lg shadow-purple-500/5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-full font-bold">
                EXPERIMENT CANDIDATE
              </span>
              <h3 className="text-base font-bold text-slate-100 mt-2">Dynamic Reliability-Weighted Policy</h3>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">{candVersion}</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Reliability Weight: {candRelWeight}</span>
                <span className="text-emerald-400">+80% vs baseline</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={candRelWeight}
                onChange={(e) => setCandRelWeight(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Lead Time Weight: {candLeadWeight}</span>
                <span className="text-slate-400">Maintained</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={candLeadWeight}
                onChange={(e) => setCandLeadWeight(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Unit Price Weight: {candPriceWeight}</span>
                <span className="text-amber-400">-50% vs baseline</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={candPriceWeight}
                onChange={(e) => setCandPriceWeight(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
          </div>

          <button
            onClick={handleRunExperiment}
            disabled={runningExperiment}
            className="w-full flex items-center justify-center space-x-2 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-purple-600/25 cursor-pointer"
          >
            {runningExperiment ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Simulating Benchmark Scenarios...</span>
              </>
            ) : (
              <>
                <FlaskConical className="w-4 h-4" />
                <span>Run Controlled Benchmark Experiment</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Latest Benchmark Results Comparison */}
      {latestExperiment && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <span className="text-xs font-mono text-purple-400 uppercase tracking-wider">
                Benchmark Evaluation Results
              </span>
              <h3 className="text-lg font-bold text-slate-100 mt-1">
                Comparative Analysis Across Fixed Holdout Scenarios
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated against: Severe Supplier Delay, Chicago Demand Surge, and Multi-Supplier Disruption
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <span className={`text-xs px-3 py-1 rounded-full font-bold flex items-center space-x-1.5 ${
                latestExperiment.comparison_summary.passes_safety_gate
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}>
                {latestExperiment.comparison_summary.passes_safety_gate ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    <span>Safety Gate Passed</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5 mr-1" />
                    <span>Safety Gate Failed</span>
                  </>
                )}
              </span>

              {latestExperiment.comparison_summary.passes_safety_gate && !latestExperiment.is_promoted && (
                <button
                  onClick={() => handlePromote(latestExperiment.id)}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  Promote to Production
                </button>
              )}
            </div>
          </div>

          {/* 4 Metric Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Stockout Rate */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Total Stockout Units</div>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {latestExperiment.candidate_metrics.total_stockout_units}
                </span>
                <span className="text-xs text-slate-500 line-through">
                  {latestExperiment.baseline_metrics.total_stockout_units}
                </span>
              </div>
              <div className="text-xs text-emerald-400 mt-2 flex items-center font-bold">
                <TrendingDown className="w-3.5 h-3.5 mr-1" />
                -{latestExperiment.comparison_summary.stockout_reduction_pct}% Stockouts
              </div>
            </div>

            {/* SLA Compliance */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">SLA Compliance Rate</div>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {Math.round(latestExperiment.candidate_metrics.sla_compliance_rate * 100)}%
                </span>
                <span className="text-xs text-slate-500 line-through">
                  {Math.round(latestExperiment.baseline_metrics.sla_compliance_rate * 100)}%
                </span>
              </div>
              <div className="text-xs text-emerald-400 mt-2 flex items-center font-bold">
                <TrendingUp className="w-3.5 h-3.5 mr-1" />
                +{latestExperiment.comparison_summary.sla_improvement_pct}% SLA Boost
              </div>
            </div>

            {/* Avg Lead Time */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Average Sourcing Lead Time</div>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-bold font-mono text-blue-400">
                  {latestExperiment.candidate_metrics.avg_lead_time_days}d
                </span>
                <span className="text-xs text-slate-500 line-through">
                  {latestExperiment.baseline_metrics.avg_lead_time_days}d
                </span>
              </div>
              <div className="text-xs text-blue-400 mt-2 flex items-center font-bold">
                <TrendingDown className="w-3.5 h-3.5 mr-1" />
                -{latestExperiment.comparison_summary.lead_time_reduction_days} Days Faster
              </div>
            </div>

            {/* Recovery Cost Trade-off */}
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Average Recovery Cost</div>
              <div className="flex items-baseline space-x-2">
                <span className="text-xl font-bold font-mono text-slate-200">
                  ${latestExperiment.candidate_metrics.avg_recovery_cost.toLocaleString()}
                </span>
                <span className="text-xs text-slate-500 line-through">
                  ${latestExperiment.baseline_metrics.avg_recovery_cost.toLocaleString()}
                </span>
              </div>
              <div className="text-xs text-amber-400 mt-2">
                +{latestExperiment.comparison_summary.cost_change_pct}% trade-off (within 15% safety limit)
              </div>
            </div>
          </div>

          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 text-xs text-slate-300">
            <span className="font-bold text-slate-100 uppercase tracking-wider mr-2">Evaluation Conclusion:</span>
            {latestExperiment.evaluation_notes}
          </div>
        </div>
      )}

      {/* Historical Experiments Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Experiment Audit Trail ({experiments.length} Runs Recorded)
          </h3>
        </div>
        <table className="w-full text-left text-xs text-slate-300 font-mono">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-sans">
            <tr>
              <th className="py-3 px-4">Version</th>
              <th className="py-3 px-4">Stockout Reduction</th>
              <th className="py-3 px-4">SLA Delta</th>
              <th className="py-3 px-4">Cost Delta</th>
              <th className="py-3 px-4">Safety Gate</th>
              <th className="py-3 px-4">Production Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {experiments.map((exp) => (
              <tr key={exp.id} className="hover:bg-slate-800/30">
                <td className="py-3 px-4 text-purple-400 font-bold">{exp.policy_version}</td>
                <td className="py-3 px-4 text-emerald-400 font-bold">
                  -{exp.comparison_summary.stockout_reduction_pct}%
                </td>
                <td className="py-3 px-4 text-slate-200">
                  +{exp.comparison_summary.sla_improvement_pct}%
                </td>
                <td className="py-3 px-4 text-slate-400">
                  +{exp.comparison_summary.cost_change_pct}%
                </td>
                <td className="py-3 px-4 font-sans">
                  {exp.comparison_summary.passes_safety_gate ? (
                    <span className="text-emerald-400 flex items-center">
                      <Check className="w-3.5 h-3.5 mr-1" /> Passed
                    </span>
                  ) : (
                    <span className="text-rose-400 flex items-center">
                      <XCircle className="w-3.5 h-3.5 mr-1" /> Rejected
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 font-sans">
                  {exp.is_promoted ? (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                      PROMOTED
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      CANDIDATE
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
