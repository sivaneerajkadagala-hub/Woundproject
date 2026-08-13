import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, PlusCircle, TrendingDown, Calendar, FileText, ArrowUpRight, GitCompare } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { WoundCase, HealingHistoryPoint } from '../types';
import api from '../services/api';

export const WoundDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [wound, setWound] = useState<WoundCase | null>(null);
  const [history, setHistory] = useState<HealingHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [wRes, hRes] = await Promise.all([
          api.get(`/wounds/${id}`),
          api.get(`/wounds/${id}/history`)
        ]);
        setWound(wRes.data);
        setHistory(hRes.data);
      } catch (err) {
        console.error('Error fetching wound case details:', err);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchData();
  }, [id]);

  if (loading || !wound) {
    return <div className="p-8 text-center text-slate-500">Loading wound case record...</div>;
  }

  // Calculate total healing reduction from first to last visit
  let overallReduction = 0;
  if (history.length > 1) {
    const initial = history[0].area_mm2;
    const latest = history[history.length - 1].area_mm2;
    if (initial > 0) {
      overallReduction = roundNum(((initial - latest) / initial) * 100);
    }
  }

  function roundNum(val: number) {
    return Math.round(val * 10) / 10;
  }

  const chartData = history.map((h) => ({
    name: `Visit ${h.visit_number}`,
    area: h.area_mm2,
    date: new Date(h.visit_date).toLocaleDateString()
  }));

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to={`/patients/${wound.patient_id}`} className="p-2 text-slate-400 hover:text-slate-700 bg-white rounded-xl border border-slate-200">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-800">
                {wound.case_code}
              </span>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{wound.location}</h2>
              <Badge status={wound.healing_status || 'Baseline'} />
            </div>
            <p className="text-xs text-slate-500">
              Patient: <span className="font-bold text-slate-700">{wound.patient_name}</span> ({wound.patient_code}) | Category: {wound.wound_type}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/compare"
            className="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-3 py-2 rounded-xl text-xs transition-colors"
          >
            <GitCompare className="w-4 h-4" />
            <span>Compare Visits</span>
          </Link>

          <Link
            to={`/assessment/new?wound_id=${wound.id}`}
            className="inline-flex items-center gap-1.5 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold px-4 py-2 rounded-xl text-xs shadow transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Visit Assessment</span>
          </Link>
        </div>
      </div>

      {/* Healing Progression Line Chart */}
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between border-b border-slate-100 pb-3 gap-2">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Longitudinal Surface Area Trajectory</h3>
            <p className="text-xs text-slate-500">Surface area measurements (mm²) across sequential visits</p>
          </div>

          {history.length > 1 && (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-emerald-600" />
              <span>Net Area Change: -{overallReduction}% ({history[0].area_mm2} mm² &rarr; {history[history.length - 1].area_mm2} mm²)</span>
            </div>
          )}
        </div>

        {chartData.length > 0 ? (
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="woundAreaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} unit=" mm²" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff' }}
                  formatter={(val: any) => [`${val} mm²`, 'Surface Area']}
                />
                <Area type="monotone" dataKey="area" stroke="#0284c7" strokeWidth={3} fillOpacity={1} fill="url(#woundAreaGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-10 text-slate-400 text-xs">
            No assessment visits recorded yet for this wound case.
          </div>
        )}
      </Card>

      {/* Visit History Table */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-bold text-slate-900 text-base">Visit Assessment History</h3>
          <span className="text-xs text-slate-400 font-mono">{history.length} visit(s) logged</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Visit</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Wound Area (mm²)</th>
                <th className="px-4 py-3">Area (cm²)</th>
                <th className="px-4 py-3">Change %</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Assessment Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.map((h) => (
                <tr key={h.visit_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3.5 font-bold text-slate-800">Visit #{h.visit_number}</td>
                  <td className="px-4 py-3.5 text-slate-600">{new Date(h.visit_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3.5 font-bold text-cyan-700">{h.area_mm2} mm²</td>
                  <td className="px-4 py-3.5 text-slate-600">{h.area_cm2} cm²</td>
                  <td className="px-4 py-3.5 font-semibold">
                    {h.percentage_change !== null && h.percentage_change !== undefined ? (
                      <span className={h.percentage_change < 0 ? 'text-emerald-600' : 'text-rose-600'}>
                        {h.percentage_change}%
                      </span>
                    ) : (
                      '--'
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <Badge status={h.healing_status} />
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      to={`/assessment/${h.visit_id}`}
                      className="font-bold text-cyan-600 hover:underline"
                    >
                      View Report
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
