import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Users, 
  Activity, 
  TrendingDown, 
  AlertCircle, 
  PlusCircle, 
  Calendar, 
  ArrowUpRight,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DashboardSummary } from '../types';
import api from '../services/api';

export const DashboardPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await api.get('/dashboard/summary');
        setSummary(res.data);
      } catch (err) {
        console.error('Error fetching dashboard summary:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  // Demo trend data for longitudinal dashboard chart
  const sampleTrend = [
    { visit: 'Visit 1', area: 320 },
    { visit: 'Visit 2', area: 275 },
    { visit: 'Visit 3', area: 230 },
    { visit: 'Visit 4', area: 195 },
  ];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-cyan-950 p-6 md:p-8 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="z-10 space-y-2">
          <div className="inline-flex items-center gap-1.5 bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-3 py-1 rounded-full text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Decision Support System</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            Wound Healing Clinical Dashboard
          </h2>
          <p className="text-xs md:text-sm text-slate-300 max-w-xl">
            Automated U-Net segmentation, calibration-based area calculation, and longitudinal progress tracking.
          </p>
        </div>

        <div className="z-10">
          <button
            onClick={() => navigate('/assessment/new')}
            className="w-full md:w-auto inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-teal-400 hover:from-cyan-400 hover:to-teal-300 text-white font-bold px-5 py-3 rounded-2xl shadow-lg shadow-cyan-500/30 transition-all duration-200"
          >
            <PlusCircle className="w-5 h-5" />
            <span>Start New Assessment</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="flex items-center gap-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl border border-blue-100">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase">Total Patients</p>
            <h3 className="text-2xl font-extrabold text-slate-900">{summary?.total_patients ?? 3}</h3>
            <span className="text-[10px] text-slate-400">Synthetic demo cohort</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-cyan-50 text-cyan-600 rounded-2xl border border-cyan-100">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase">Active Wounds</p>
            <h3 className="text-2xl font-extrabold text-slate-900">{summary?.active_wounds ?? 2}</h3>
            <span className="text-[10px] text-cyan-600 font-semibold">Under monitoring</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl border border-teal-100">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase">Total Visits</p>
            <h3 className="text-2xl font-extrabold text-slate-900">{summary?.total_measurements ?? 4}</h3>
            <span className="text-[10px] text-slate-400">Assessments recorded</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl border border-emerald-100">
            <TrendingDown className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase">Wounds Improving</p>
            <h3 className="text-2xl font-extrabold text-emerald-600">{summary?.improving_wounds ?? 3}</h3>
            <span className="text-[10px] text-emerald-600 font-semibold">Area reducing</span>
          </div>
        </Card>

        <Card className="flex items-center gap-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-2xl border border-amber-100">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase">Needs Attention</p>
            <h3 className="text-2xl font-extrabold text-amber-600">{summary?.attention_wounds ?? 0}</h3>
            <span className="text-[10px] text-slate-400">Stable / Increasing</span>
          </div>
        </Card>
      </div>

      {/* Main Content Grid: Healing Trend Chart & Quick Start */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Longitudinal Chart */}
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Wound Healing Trajectory (Sample)</h3>
              <p className="text-xs text-slate-500">Average surface area reduction (mm²) over sequential visits</p>
            </div>
            <span className="bg-emerald-50 text-emerald-700 text-xs px-2.5 py-1 rounded-full font-bold border border-emerald-200">
              -39% Overall Reduction
            </span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sampleTrend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="visit" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} unit=" mm²" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', color: '#fff' }}
                  formatter={(val: any) => [`${val} mm²`, 'Surface Area']}
                />
                <Area type="monotone" dataKey="area" stroke="#0284c7" strokeWidth={3} fillOpacity={1} fill="url(#colorArea)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Quick Actions & Demo Info */}
        <div className="space-y-4">
          <Card className="bg-slate-900 text-white space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-cyan-400" />
              <h4 className="font-bold text-base">Quick Clinical Actions</h4>
            </div>

            <div className="space-y-2">
              <Link
                to="/assessment/new"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 transition-colors border border-slate-700 text-xs font-semibold text-slate-200"
              >
                <span>Process Wound Photograph</span>
                <ArrowUpRight className="w-4 h-4 text-cyan-400" />
              </Link>
              <Link
                to="/patients"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 transition-colors border border-slate-700 text-xs font-semibold text-slate-200"
              >
                <span>View Synthetic Patients</span>
                <ArrowUpRight className="w-4 h-4 text-cyan-400" />
              </Link>
              <Link
                to="/compare"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 transition-colors border border-slate-700 text-xs font-semibold text-slate-200"
              >
                <span>Side-by-Side Visit Comparison</span>
                <ArrowUpRight className="w-4 h-4 text-cyan-400" />
              </Link>
              <Link
                to="/assistant"
                className="flex items-center justify-between p-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 transition-colors border border-slate-700 text-xs font-semibold text-slate-200"
              >
                <span>Consult AI Assistant</span>
                <ArrowUpRight className="w-4 h-4 text-cyan-400" />
              </Link>
            </div>
          </Card>
        </div>
      </div>

      {/* Recent Assessments Table */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Recent Wound Assessments</h3>
            <p className="text-xs text-slate-500">Latest recorded assessments across patient cases</p>
          </div>
          <Link to="/patients" className="text-xs font-semibold text-cyan-600 hover:underline">
            View All Patients &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Visit Date</th>
                <th className="px-4 py-3">Wound Area</th>
                <th className="px-4 py-3">Trajectory</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary?.recent_assessments && summary.recent_assessments.length > 0 ? (
                summary.recent_assessments.map((a) => (
                  <tr key={a.visit_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3.5 font-bold text-slate-800">
                      {a.patient_code} - {a.patient_name}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-cyan-700 font-semibold">{a.case_code}</td>
                    <td className="px-4 py-3.5 text-slate-600">{a.location}</td>
                    <td className="px-4 py-3.5 text-slate-500">{new Date(a.visit_date).toLocaleDateString()}</td>
                    <td className="px-4 py-3.5 font-bold text-slate-900">{a.area_mm2} mm²</td>
                    <td className="px-4 py-3.5">
                      <Badge status={a.healing_status} />
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <Link
                        to={`/assessment/${a.visit_id}`}
                        className="text-cyan-600 font-semibold hover:underline"
                      >
                        View Detail
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-slate-400">
                    No recent assessments recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
