import React, { useEffect, useState } from 'react';
import {
  AlertTriangle, CheckCircle, Clock, DollarSign, Package,
  ShieldAlert, TrendingUp, Warehouse as WarehouseIcon, ArrowRight
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, LineChart, Line, Legend
} from 'recharts';
import { DashboardOverview, Warehouse, Supplier } from '../types';
import { api } from '../services/api';

interface Props {
  onNavigate: (tab: string) => void;
  onSelectIncident?: (incidentId: number) => void;
}

export const CommandCenter: React.FC<Props> = ({ onNavigate, onSelectIncident }) => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dash, whs, sups] = await Promise.all([
        api.getDashboard(),
        api.getWarehouses(),
        api.getSuppliers()
      ]);
      setData(dash);
      setWarehouses(whs);
      setSuppliers(sups);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Clock className="w-6 h-6 animate-spin mr-2" />
        Loading Operations Command Center...
      </div>
    );
  }

  const warehouseChartData = warehouses.map(w => ({
    name: w.code,
    utilization: Math.round(w.current_utilization),
    capacity: w.capacity_units / 1000
  }));

  const supplierChartData = suppliers.map(s => ({
    name: s.code.replace('SUP-', ''),
    otif: Math.round(s.on_time_delivery_rate * 100),
    leadTime: s.avg_lead_time_days
  }));

  return (
    <div className="space-y-6">
      {/* Top Banner Alert if active disruption */}
      {data.active_disruptions > 0 && (
        <div className="bg-amber-950/40 border border-amber-600/40 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="font-semibold text-amber-200">
                Critical Supply Chain Disruption Detected: {data.recent_incidents[0]?.title}
              </div>
              <div className="text-sm text-amber-300/80">
                Inbound delivery delayed by 7 days. {data.orders_at_risk_count} customer orders (${data.revenue_at_risk.toLocaleString()} revenue) at immediate stockout risk.
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigate('task-console')}
            className="flex items-center space-x-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-medium rounded-lg text-sm transition-all shadow-lg shadow-amber-500/20"
          >
            <span>Launch ORBIT Investigation</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Inventory Value */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Total Inventory Value</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            ${data.total_inventory_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center">
            <WarehouseIcon className="w-3.5 h-3.5 mr-1 text-slate-400" />
            Across {data.total_warehouses} regional distribution hubs
          </div>
        </div>

        {/* Orders & Revenue at Risk */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Orders at Risk</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400">
            {data.orders_at_risk_count} Orders
          </div>
          <div className="text-xs text-rose-300/80 mt-2">
            ${data.revenue_at_risk.toLocaleString()} exposed customer revenue
          </div>
        </div>

        {/* Supplier Network Reliability */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Supplier Reliability (OTIF)</span>
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {Math.round(data.avg_supplier_reliability * 100)}%
          </div>
          <div className="text-xs text-slate-400 mt-2">
            {data.total_suppliers} tier-1 & tier-2 verified vendors
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold tracking-wider uppercase">Pending Actions</span>
            <CheckCircle className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-400">
            {data.pending_approvals} Approvals
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Requires human authorization to dispatch
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Warehouse Capacities & Utilization */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-200">Warehouse Utilization & Capacity</h3>
              <p className="text-xs text-slate-400">Current storage occupancy across regional facilities</p>
            </div>
            <span className="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md">Live Storage</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={warehouseChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" textAnchor="end" tick={{ fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Bar dataKey="utilization" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Occupancy %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Supplier Performance Comparison */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-200">Supplier OTIF Reliability & Lead Times</h3>
              <p className="text-xs text-slate-400">On-time in-full delivery rate vs average lead time (days)</p>
            </div>
            <span className="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded-md">Vendor Matrix</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={supplierChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="otif" fill="#10b981" radius={[4, 4, 0, 0]} name="OTIF Delivery %" />
                <Bar dataKey="leadTime" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Lead Time (Days)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Operational Incidents Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-200">Active Operational Incidents</h3>
            <p className="text-xs text-slate-400">Real-time alerts requiring multi-agent operations intelligence</p>
          </div>
          <button
            onClick={() => onNavigate('disruption-investigation')}
            className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center"
          >
            View All Incidents <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 text-xs uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Incident ID</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Title & Context</th>
                <th className="py-3 px-4">Disrupted Entity</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {data.recent_incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-mono text-xs text-blue-400">{inc.incident_key}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                      inc.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                      inc.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                      'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-medium text-slate-200">{inc.title}</div>
                    <div className="text-xs text-slate-400 truncate max-w-md">{inc.description}</div>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-300">
                    {inc.affected_supplier_name || inc.affected_warehouse_name || 'Supply Network'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {inc.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => onNavigate('task-console')}
                      className="px-3 py-1 bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 text-xs rounded transition-colors"
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
