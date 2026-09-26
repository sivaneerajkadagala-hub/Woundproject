import React, { useState, useEffect } from 'react';
import { FileText, Download, ShieldCheck, Printer, CheckCircle } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Patient, WoundCase } from '../types';
import api from '../services/api';

export const ReportsPage: React.FC = () => {
  const [recentAssessments, setRecentAssessments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await api.get('/dashboard/summary');
        setRecentAssessments(res.data.recent_assessments || []);
      } catch (err) {
        console.error('Error loading reports:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const downloadPdf = async (visitId: number) => {
    try {
      const token = localStorage.getItem('wound_ai_token');
      const response = await fetch(`/api/reports/${visitId}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) {
        throw new Error(`Failed to generate PDF (status ${response.status})`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = `Wound_Report_Visit_${visitId}.pdf`;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF download error:', err);
      alert('Failed to download PDF report. Please try again.');
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <FileText className="w-6 h-6 text-cyan-600" />
          <span>Clinical Assessment Reports</span>
        </h2>
        <p className="text-xs text-slate-500">Export formatted PDF decision-support reports containing image masks, overlays, and metrics</p>
      </div>

      {/* Notice Card */}
      <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 flex items-center gap-3">
        <ShieldCheck className="w-6 h-6 text-cyan-400 shrink-0" />
        <div className="text-xs space-y-0.5">
          <p className="font-bold text-slate-200">Standardized PDF Export Engine</p>
          <p className="text-slate-400">
            Reports include patient code, anatomical wound location, calibration scale, segmentation score, surface area (mm² / cm²), and medical disclaimer.
          </p>
        </div>
      </div>

      {/* Reports Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="px-6 py-3.5">Visit ID</th>
                <th className="px-6 py-3.5">Patient Code</th>
                <th className="px-6 py-3.5">Wound Case</th>
                <th className="px-6 py-3.5">Visit Date</th>
                <th className="px-6 py-3.5">Area Measurement</th>
                <th className="px-6 py-3.5 text-right">PDF Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentAssessments.length > 0 ? (
                recentAssessments.map((a) => (
                  <tr key={a.visit_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-900">Visit #{a.visit_id}</td>
                    <td className="px-6 py-4 font-mono font-bold text-cyan-700">{a.patient_code}</td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{a.case_code} ({a.location})</td>
                    <td className="px-6 py-4 text-slate-500">{new Date(a.visit_date).toLocaleDateString()}</td>
                    <td className="px-6 py-4 font-bold text-slate-900">{a.area_mm2} mm²</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => downloadPdf(a.visit_id)}
                        className="inline-flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold px-3 py-1.5 rounded-xl text-xs transition-colors"
                      >
                        <Download className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Download PDF</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    No assessment records found for report generation.
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
