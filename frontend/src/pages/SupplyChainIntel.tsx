import React, { useState, useEffect } from 'react';
import {
  Package, Truck, TrendingUp, AlertCircle, Search, Filter,
  Calendar, DollarSign, Warehouse as WarehouseIcon
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { InventoryDetail, Supplier, PurchaseOrder, Product } from '../types';
import { api } from '../services/api';

export const SupplyChainIntel: React.FC = () => {
  const [subTab, setSubTab] = useState<'inventory' | 'suppliers' | 'demand' | 'pos'>('inventory');
  const [inventory, setInventory] = useState<InventoryDetail[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [demandData, setDemandData] = useState<Array<{ date: string; demand_qty: number }>>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIntel();
  }, []);

  const loadIntel = async () => {
    setLoading(true);
    try {
      const [inv, sups, pos, dem] = await Promise.all([
        api.getInventory(),
        api.getSuppliers(),
        api.getPurchaseOrders(),
        api.getDemandHistory(1, 1)
      ]);
      setInventory(inv);
      setSuppliers(sups);
      setPurchaseOrders(pos);
      setDemandData(dem);
    } catch (err) {
      console.error('Failed to load supply chain intel:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredInventory = inventory.filter(
    item => item.product_sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.warehouse_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Controls & Navigation Subtabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Supply Chain Operations Intelligence</h2>
          <p className="text-xs text-slate-400">Multi-echelon inventory runway, vendor reliability, and demand history</p>
        </div>

        <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setSubTab('inventory')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              subTab === 'inventory' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Inventory Ledger
          </button>
          <button
            onClick={() => setSubTab('suppliers')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              subTab === 'suppliers' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Vendor Reliability
          </button>
          <button
            onClick={() => setSubTab('demand')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              subTab === 'demand' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Demand Analytics
          </button>
          <button
            onClick={() => setSubTab('pos')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              subTab === 'pos' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Purchase Orders
          </button>
        </div>
      </div>

      {/* Subtab 1: Inventory Ledger */}
      {subTab === 'inventory' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="relative w-72">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search SKU, product or warehouse..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="text-xs text-slate-400">
              Showing {filteredInventory.length} SKU-warehouse positions
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Warehouse</th>
                    <th className="py-3 px-4">SKU & Product</th>
                    <th className="py-3 px-4 text-right">On Hand</th>
                    <th className="py-3 px-4 text-right">Reserved</th>
                    <th className="py-3 px-4 text-right">Available</th>
                    <th className="py-3 px-4 text-right">Safety Stock</th>
                    <th className="py-3 px-4 text-right">Runway Days</th>
                    <th className="py-3 px-4 text-right">Total Value</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredInventory.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-semibold text-slate-200">{item.warehouse_code}</span>
                        <div className="text-[10px] text-slate-500 font-sans">{item.warehouse_name}</div>
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span className="font-mono text-blue-400 font-semibold">{item.product_sku}</span>
                        <div className="text-slate-300 text-xs truncate max-w-xs">{item.product_name}</div>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-200">{item.on_hand_qty}</td>
                      <td className="py-3 px-4 text-right text-slate-400">{item.reserved_qty}</td>
                      <td className="py-3 px-4 text-right text-slate-300">{item.available_qty}</td>
                      <td className="py-3 px-4 text-right text-slate-400">{item.safety_stock}</td>
                      <td className="py-3 px-4 text-right font-bold">
                        <span className={item.runway_days < 5 ? 'text-rose-400' : item.runway_days < 10 ? 'text-amber-400' : 'text-emerald-400'}>
                          {item.runway_days}d
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        ${item.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center font-sans">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          item.stockout_risk === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                          item.stockout_risk === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                          'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {item.stockout_risk}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Subtab 2: Supplier Matrix */}
      {subTab === 'suppliers' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Vendor Code</th>
                <th className="py-3 px-4">Supplier Name</th>
                <th className="py-3 px-4">Tier</th>
                <th className="py-3 px-4 text-right">Reliability Score</th>
                <th className="py-3 px-4 text-right">Avg Lead Time</th>
                <th className="py-3 px-4 text-right">OTIF Delivery Rate</th>
                <th className="py-3 px-4 text-right">Quality Score</th>
                <th className="py-3 px-4">Contact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {suppliers.map((sup) => (
                <tr key={sup.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 text-blue-400 font-bold">{sup.code}</td>
                  <td className="py-3 px-4 font-sans font-medium text-slate-200">{sup.name}</td>
                  <td className="py-3 px-4 font-sans">
                    <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 rounded">
                      {sup.tier}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-bold">
                    {Math.round(sup.reliability_score * 100)}%
                  </td>
                  <td className="py-3 px-4 text-right text-slate-200">{sup.avg_lead_time_days} Days</td>
                  <td className="py-3 px-4 text-right text-slate-300">
                    {Math.round(sup.on_time_delivery_rate * 100)}%
                  </td>
                  <td className="py-3 px-4 text-right text-amber-400 font-bold">
                    {sup.quality_rating} / 5.0
                  </td>
                  <td className="py-3 px-4 font-sans text-slate-400 text-[11px]">{sup.contact_email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Subtab 3: Demand Analytics */}
      {subTab === 'demand' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Historical Demand Trajectory (Past 30 Days)</h3>
              <p className="text-xs text-slate-400">SKU P-MOT-100 High-Torque Servo Motor at Chicago Distribution Center</p>
            </div>
            <div className="text-xs font-mono text-blue-400">
              Avg Daily Run Rate: ~12.4 Units
            </div>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={demandData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="demand_qty" stroke="#3b82f6" strokeWidth={2} name="Daily Demand" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Subtab 4: Purchase Orders */}
      {subTab === 'pos' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">PO Number</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4">Warehouse</th>
                <th className="py-3 px-4">Expected Date</th>
                <th className="py-3 px-4">Revised Date</th>
                <th className="py-3 px-4 text-center">Delay</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Total Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {purchaseOrders.map((po) => (
                <tr key={po.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 text-blue-400 font-bold">{po.po_number}</td>
                  <td className="py-3 px-4 font-sans text-slate-200">{po.supplier_name}</td>
                  <td className="py-3 px-4 font-sans text-slate-300">{po.warehouse_name}</td>
                  <td className="py-3 px-4 text-slate-400">{po.expected_delivery_date}</td>
                  <td className="py-3 px-4 text-slate-300">{po.revised_delivery_date || '—'}</td>
                  <td className="py-3 px-4 text-center">
                    {po.delay_days > 0 ? (
                      <span className="text-rose-400 font-bold">+{po.delay_days}d</span>
                    ) : (
                      <span className="text-emerald-400 font-normal">0d</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-sans">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                      po.status === 'DELAYED' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                      po.status === 'CONFIRMED' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                      'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {po.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-slate-200">
                    ${po.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
