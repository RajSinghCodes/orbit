import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, Terminal, Cpu, Database, ShieldAlert,
  Sliders, FlaskConical, Activity, CheckCircle2, RotateCcw
} from 'lucide-react';
import { CommandCenter } from './pages/CommandCenter';
import { TaskConsole } from './pages/TaskConsole';
import { AgentExecution } from './pages/AgentExecution';
import { SupplyChainIntel } from './pages/SupplyChainIntel';
import { DisruptionInvestigation } from './pages/DisruptionInvestigation';
import { RecoveryPlanApprovals } from './pages/RecoveryPlanApprovals';
import { SelfImprovementLab } from './pages/SelfImprovementLab';
import { ObservabilityTraces } from './pages/ObservabilityTraces';
import { Workflow } from './types';
import { api } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('command-center');
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow | null>(null);
  const [systemHealth, setSystemHealth] = useState<{ status: string; platform: string; llm_mode: string } | null>(null);

  useEffect(() => {
    checkHealthAndLoadLatest();
  }, []);

  const checkHealthAndLoadLatest = async () => {
    try {
      const health = await api.checkHealth();
      setSystemHealth(health);
      const wfs = await api.listWorkflows();
      if (wfs.length > 0) {
        setActiveWorkflow(wfs[0]);
      }
    } catch (err) {
      console.warn('Backend connection pending...');
    }
  };

  const navItems = [
    { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
    { id: 'task-console', label: 'Task Console', icon: Terminal },
    { id: 'live-agents', label: 'Live Agent Execution', icon: Cpu },
    { id: 'supply-chain', label: 'Supply Chain Intel', icon: Database },
    { id: 'disruption-investigation', label: 'Disruption Analysis', icon: ShieldAlert },
    { id: 'recovery-plans', label: 'Recovery & Approvals', icon: Sliders },
    { id: 'self-improvement', label: 'Self-Improvement Lab', icon: FlaskConical },
    { id: 'observability', label: 'Observability & Traces', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Enterprise Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-blue-500/20">
              O
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white">ORBIT</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-semibold">
                  OPERATIONS AI
                </span>
              </div>
              <p className="text-[10px] text-slate-400 -mt-0.5">Autonomous Business Operations Intelligence</p>
            </div>
          </div>

          {/* System Status Indicators */}
          <div className="hidden md:flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>LangGraph Multi-Agent DAG</span>
            </div>
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              <span>Deterministic Optimizer Active</span>
            </div>
            <div className="text-slate-500 text-[11px]">
              Mode: <span className="text-slate-300">{systemHealth?.llm_mode || 'autonomous'}</span>
            </div>
          </div>
        </div>

        {/* 8 Specialized Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center space-x-1 overflow-x-auto no-scrollbar border-t border-slate-800/40">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all shrink-0 cursor-pointer ${
                  isActive
                    ? 'border-blue-500 text-blue-400 bg-blue-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'command-center' && (
          <CommandCenter onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'task-console' && (
          <TaskConsole
            onNavigate={(tab) => setActiveTab(tab)}
            onWorkflowSelected={(wf) => setActiveWorkflow(wf)}
            activeWorkflow={activeWorkflow}
          />
        )}
        {activeTab === 'live-agents' && (
          <AgentExecution activeWorkflow={activeWorkflow} />
        )}
        {activeTab === 'supply-chain' && (
          <SupplyChainIntel />
        )}
        {activeTab === 'disruption-investigation' && (
          <DisruptionInvestigation onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'recovery-plans' && (
          <RecoveryPlanApprovals
            activeWorkflow={activeWorkflow}
            onRefreshWorkflow={checkHealthAndLoadLatest}
          />
        )}
        {activeTab === 'self-improvement' && (
          <SelfImprovementLab />
        )}
        {activeTab === 'observability' && (
          <ObservabilityTraces />
        )}
      </main>

      {/* Operational Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>ORBIT Platform · Engineering Standard for Autonomous Multi-Agent Operations</span>
          <span className="font-mono text-[11px]">Minimum User Effort · Grounded Numerical Optimization · Closed-Loop Experimentation</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
