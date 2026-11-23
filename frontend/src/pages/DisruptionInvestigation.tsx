import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, AlertTriangle, CheckCircle, HelpCircle, FileText,
  Clock, ArrowRight, DollarSign, Package, TrendingDown
} from 'lucide-react';
import { OperationalIncident } from '../types';
import { api } from '../services/api';

interface Props {
  onNavigate: (tab: string) => void;
}

export const DisruptionInvestigation: React.FC<Props> = ({ onNavigate }) => {
  const [incidents, setIncidents] = useState<OperationalIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<OperationalIncident | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.getIncidents();
      setIncidents(data);
      if (data.length > 0) {
        setSelectedIncident(data[0]);
      }
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !selectedIncident) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Clock className="w-6 h-6 animate-spin mr-2" />
        Loading Disruption Investigations...
      </div>
    );
  }

  const details = selectedIncident.details_json || {};

  return (
    <div className="space-y-6">
      {/* Page Title & Incident Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-rose-400 mb-1">
            <span>Operational Incident {selectedIncident.incident_key}</span>
            <span>·</span>
            <span>Severity: {selectedIncident.severity}</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">{selectedIncident.title}</h2>
        </div>

        <button
          onClick={() => onNavigate('task-console')}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-medium transition-all shadow-md shadow-blue-600/20"
        >
          <span>Coordinate Autonomous Response</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Primary Disruption Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Inbound PO Reference</div>
          <div className="text-lg font-mono font-bold text-blue-400">{details.po_number || 'N/A'}</div>
          <div className="text-xs text-slate-500 mt-1">{selectedIncident.affected_supplier_name || 'Primary Supplier'}</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Delayed Quantity</div>
          <div className="text-lg font-mono font-bold text-rose-400">
            {details.quantity_delayed != null ? `${details.quantity_delayed} Units` : 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">SKU {details.product_sku || 'N/A'}</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Disruption Window</div>
          <div className="text-lg font-mono font-bold text-amber-400">
            {details.delay_days != null ? `+${details.delay_days} Days` : 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Revised arrival beyond stockout</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">Immediate Financial Exposure</div>
          <div className="text-lg font-mono font-bold text-rose-400">
            {details.revenue_at_risk != null
              ? details.revenue_at_risk.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
              : 'Data Unavailable'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {details.orders_at_risk_count != null
              ? `${details.orders_at_risk_count} committed customer orders`
              : 'Order exposure pending'}
          </div>
        </div>
      </div>

      {/* Incident Root Cause Analysis */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Root-Cause Evidence</h3>
        <p className="text-sm text-slate-300 leading-relaxed">
          {selectedIncident.description}
        </p>
        <div className="text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800/80 font-mono mt-2">
          Diagnostic Evidence: Supplier {selectedIncident.affected_supplier_name || 'disrupted supplier'} reported facility constraints. Export customs hold currently active at port of departure. Confirmed delay +{details.delay_days ?? 7} calendar days.
        </div>
      </div>

      {/* Four-Quadrant Information Reliability Classification */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Evidence Grounding & Information Certainty Classification
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Quadrant 1: Confirmed Information */}
          <div className="bg-slate-900/80 border border-emerald-900/40 rounded-xl p-4 space-y-2">
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
              <CheckCircle className="w-4 h-4" />
              <span>Confirmed Information (Database & Verified EDI)</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>Inbound {details.po_number || 'PO'} revised arrival date pushed by {details.delay_days ?? 7} calendar days.</li>
              <li>{selectedIncident.affected_warehouse_name || 'Warehouse'} on-hand inventory is {details.on_hand_qty != null ? `${details.on_hand_qty} units` : 'N/A'} (Safety stock: {details.safety_stock != null ? `${details.safety_stock} units` : 'N/A'}, Available: {details.available_qty != null ? `${details.available_qty} units` : 'N/A'}).</li>
              <li>{details.orders_at_risk_count != null ? `${details.orders_at_risk_count} committed customer orders scheduled within the disruption window.` : 'Customer orders pending calculation.'}</li>
              <li>Total confirmed order quantity at risk: {details.quantity_at_risk != null ? `${details.quantity_at_risk} units` : 'N/A'} ({details.revenue_at_risk != null ? details.revenue_at_risk.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : 'N/A'} revenue).</li>
            </ul>
          </div>

          {/* Quadrant 2: Estimated Information */}
          <div className="bg-slate-900/80 border border-blue-900/40 rounded-xl p-4 space-y-2">
            <div className="flex items-center space-x-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
              <Clock className="w-4 h-4" />
              <span>Estimated Information (Predictive Models)</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>{selectedIncident.affected_warehouse_name || 'Warehouse'} daily depletion velocity estimated at {details.daily_velocity != null ? `${details.daily_velocity.toFixed(1)} units/day` : 'N/A'} (Source: {details.velocity_source || 'Demand Model'}).</li>
              <li>Projected inventory depletion cliff: {details.runway_days != null ? (details.runway_days >= 999 ? 'No projected stockout' : `Complete stockout in ${details.runway_days.toFixed(1)} business days (${details.stockout_date || 'Date Pending'})`) : 'Data Unavailable'}.</li>
              <li>Alternative supplier Nexus Precision capable of 3-day turnaround delivery.</li>
            </ul>
          </div>

          {/* Quadrant 3: Missing Information */}
          <div className="bg-slate-900/80 border border-amber-900/40 rounded-xl p-4 space-y-2">
            <div className="flex items-center space-x-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" />
              <span>Missing Information (Uncertainty Flags)</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>Whether Apex Industrial second scheduled shipment in 14 days will also be impacted.</li>
              <li>Whether affected Tier-1 VIP customers will cancel contracts or accept 48h staggered split shipments.</li>
              <li>Exact interstate line-haul freight spot pricing from Dallas to Chicago.</li>
            </ul>
          </div>

          {/* Quadrant 4: Assumptions */}
          <div className="bg-slate-900/80 border border-purple-900/40 rounded-xl p-4 space-y-2">
            <div className="flex items-center space-x-2 text-purple-400 text-xs font-bold uppercase tracking-wider">
              <HelpCircle className="w-4 h-4" />
              <span>Operational Assumptions</span>
            </div>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>Current {details.on_hand_qty != null ? `${details.on_hand_qty} on-hand units` : 'inventory'} in {selectedIncident.affected_warehouse_name || 'warehouse'} is assumed in 100% operational condition.</li>
              <li>Sister warehouse Dallas Hub will release up to 45 surplus units without dropping below safety stock.</li>
              <li>Customer order required delivery dates are strict SLAs with financial penalty clauses.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
