import React, { useState, useEffect } from 'react';
import { GitCompare, Calendar } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { SideBySideComparer } from '../components/compare/SideBySideComparer';
import { Patient, WoundCase, HealingHistoryPoint } from '../types';
import api from '../services/api';

export const CompareVisitsPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [wounds, setWounds] = useState<WoundCase[]>([]);
  const [history, setHistory] = useState<HealingHistoryPoint[]>([]);

  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [selectedWoundId, setSelectedWoundId] = useState<string>('');
  const [visitAId, setVisitAId] = useState<string>('');
  const [visitBId, setVisitBId] = useState<string>('');

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await api.get('/patients');
        setPatients(res.data);
        if (res.data.length > 0) setSelectedPatientId(res.data[0].id.toString());
      } catch (err) {
        console.error('Error fetching patients:', err);
      }
    };
    fetchPatients();
  }, []);

  useEffect(() => {
    const fetchWounds = async () => {
      if (!selectedPatientId) return;
      try {
        const res = await api.get('/wounds', { params: { patient_id: selectedPatientId } });
        setWounds(res.data);
        if (res.data.length > 0) setSelectedWoundId(res.data[0].id.toString());
      } catch (err) {
        console.error('Error fetching wounds:', err);
      }
    };
    fetchWounds();
  }, [selectedPatientId]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!selectedWoundId) return;
      try {
        const res = await api.get(`/wounds/${selectedWoundId}/history`);
        setHistory(res.data);
        if (res.data.length >= 2) {
          setVisitAId(res.data[0].visit_id.toString());
          setVisitBId(res.data[res.data.length - 1].visit_id.toString());
        } else if (res.data.length === 1) {
          setVisitAId(res.data[0].visit_id.toString());
          setVisitBId(res.data[0].visit_id.toString());
        }
      } catch (err) {
        console.error('Error fetching history:', err);
      }
    };
    fetchHistory();
  }, [selectedWoundId]);

  const visitAObj = history.find((h) => h.visit_id.toString() === visitAId);
  const visitBObj = history.find((h) => h.visit_id.toString() === visitBId);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <GitCompare className="w-6 h-6 text-cyan-600" />
          <span>Side-by-Side Visit Comparison</span>
        </h2>
        <p className="text-xs text-slate-500">Compare surface area, overlays, and percentage reduction between any two visits</p>
      </div>

      {/* Selectors */}
      <Card className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Patient</label>
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold"
          >
            {patients.map((p) => (
              <option key={p.id} value={p.id}>{p.patient_code} - {p.full_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Wound Case</label>
          <select
            value={selectedWoundId}
            onChange={(e) => setSelectedWoundId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold"
          >
            {wounds.map((w) => (
              <option key={w.id} value={w.id}>{w.case_code} - {w.location}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Compare Visit A (Baseline)</label>
          <select
            value={visitAId}
            onChange={(e) => setVisitAId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-cyan-700"
          >
            {history.map((h) => (
              <option key={h.visit_id} value={h.visit_id}>Visit #{h.visit_number} ({h.area_mm2} mm²)</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Compare Visit B (Follow-up)</label>
          <select
            value={visitBId}
            onChange={(e) => setVisitBId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-emerald-700"
          >
            {history.map((h) => (
              <option key={h.visit_id} value={h.visit_id}>Visit #{h.visit_number} ({h.area_mm2} mm²)</option>
            ))}
          </select>
        </div>
      </Card>

      {/* Comparison View */}
      {visitAObj && visitBObj ? (
        <SideBySideComparer visitA={visitAObj} visitB={visitBObj} />
      ) : (
        <div className="text-center py-12 text-slate-400 text-xs">
          Select a wound case with recorded assessment visits to compare.
        </div>
      )}
    </div>
  );
};
