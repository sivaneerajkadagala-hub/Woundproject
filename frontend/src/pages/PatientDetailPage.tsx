import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, PlusCircle, Activity, FileText, ArrowRight, ShieldCheck } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { Patient, WoundCase } from '../types';
import api from '../services/api';

export const PatientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [wounds, setWounds] = useState<WoundCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [isWoundModalOpen, setIsWoundModalOpen] = useState(false);

  // New Wound Form
  const [location, setLocation] = useState('Left lower leg');
  const [woundType, setWoundType] = useState('Venous Ulcer');
  const [notes, setNotes] = useState('');

  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      const [pRes, wRes] = await Promise.all([
        api.get(`/patients/${id}`),
        api.get('/wounds', { params: { patient_id: id } })
      ]);
      setPatient(pRes.data);
      setWounds(wRes.data);
    } catch (err) {
      console.error('Error fetching patient details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchData();
  }, [id]);

  const handleCreateWound = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      const res = await api.post('/wounds', {
        patient_id: Number(id),
        location,
        wound_type: woundType,
        notes
      });
      setIsWoundModalOpen(false);
      fetchData();
      navigate(`/wounds/${res.data.id}`);
    } catch (err) {
      console.error('Error creating wound case:', err);
    }
  };

  if (loading || !patient) {
    return <div className="p-8 text-center text-slate-500">Loading patient record...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div className="flex items-center gap-3">
        <Link to="/patients" className="p-2 text-slate-400 hover:text-slate-700 bg-white rounded-xl border border-slate-200">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{patient.full_name}</h2>
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-800">
              {patient.patient_code}
            </span>
          </div>
          <p className="text-xs text-slate-500">Patient Demographic Profile & Wound Cases</p>
        </div>
      </div>

      {/* Patient Profile Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-bold text-slate-900 text-sm">Demographics</h3>
            <ShieldCheck className="w-4 h-4 text-cyan-600" />
          </div>

          <div className="space-y-2 text-xs">
            <div>
              <span className="text-slate-400 font-semibold block">Synthetic ID</span>
              <span className="font-mono font-bold text-slate-800 text-sm">{patient.patient_code}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold block">Age / Gender</span>
              <span className="text-slate-800 font-medium">{patient.age ?? 'N/A'} years / {patient.gender ?? 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400 font-semibold block">Clinical Notes</span>
              <p className="text-slate-600 leading-relaxed mt-0.5">{patient.medical_notes || 'No notes documented.'}</p>
            </div>
          </div>
        </Card>

        {/* Wound Cases List */}
        <Card className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Wound Cases ({wounds.length})</h3>
              <p className="text-xs text-slate-500">Active and historical wound assessments</p>
            </div>

            <button
              onClick={() => setIsWoundModalOpen(true)}
              className="inline-flex items-center gap-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-3 py-1.5 rounded-xl text-xs transition-colors"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New Wound Case</span>
            </button>
          </div>

          <div className="space-y-3">
            {wounds.length > 0 ? (
              wounds.map((w) => (
                <div
                  key={w.id}
                  className="p-4 rounded-xl border border-slate-200 hover:border-cyan-300 bg-slate-50/50 hover:bg-slate-50 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-cyan-700 text-xs">{w.case_code}</span>
                      <h4 className="font-bold text-slate-900 text-sm">{w.location}</h4>
                      <Badge status={w.healing_status || 'Baseline'} />
                    </div>
                    <p className="text-xs text-slate-500">Category: {w.wound_type} | Visits: {w.visits_count}</p>
                    {w.latest_area_mm2 && (
                      <p className="text-xs font-bold text-slate-800">Latest Surface Area: {w.latest_area_mm2} mm²</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      to={`/wounds/${w.id}`}
                      className="inline-flex items-center gap-1 bg-white hover:bg-slate-100 text-cyan-700 font-bold px-3 py-1.5 rounded-lg border border-slate-200 text-xs transition-colors"
                    >
                      <span>Open Case</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs">
                No wound cases registered for this patient. Click "New Wound Case" to add one.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* New Wound Case Modal */}
      <Modal isOpen={isWoundModalOpen} onClose={() => setIsWoundModalOpen(false)} title="Create New Wound Case">
        <form onSubmit={handleCreateWound} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Anatomical Location</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-cyan-500"
            >
              <option value="Left lower leg">Left lower leg</option>
              <option value="Right foot">Right foot</option>
              <option value="Forearm">Forearm</option>
              <option value="Heel">Heel</option>
              <option value="Sacrum / Pressure Site">Sacrum / Pressure Site</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Wound Category / Type</label>
            <select
              value={woundType}
              onChange={(e) => setWoundType(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-cyan-500"
            >
              <option value="Venous Ulcer">Venous Ulcer</option>
              <option value="Diabetic Foot Ulcer">Diabetic Foot Ulcer</option>
              <option value="Pressure Injury">Pressure Injury</option>
              <option value="Surgical Wound">Surgical Wound</option>
              <option value="Arterial Ulcer">Arterial Ulcer</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Case Notes</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Initial clinical description..."
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-cyan-500"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs rounded-xl shadow transition-colors"
          >
            Save Wound Case
          </button>
        </form>
      </Modal>
    </div>
  );
};
