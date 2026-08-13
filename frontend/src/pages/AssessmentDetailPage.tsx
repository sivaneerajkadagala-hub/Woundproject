import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileText, Download, CheckCircle, ShieldAlert, Cpu } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { MaskViewer } from '../components/assessment/MaskViewer';
import { AssessmentDetail } from '../types';
import api from '../services/api';

export const AssessmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAssessment = async () => {
      try {
        const res = await api.get(`/assessments/${id}`);
        setAssessment(res.data);
      } catch (err) {
        console.error('Error fetching assessment detail:', err);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchAssessment();
  }, [id]);

  if (loading || !assessment) {
    return <div className="p-8 text-center text-slate-500">Loading visit assessment record...</div>;
  }

  const downloadPdf = () => {
    window.open(`/api/reports/${assessment.visit_id}/download`, '_blank');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to={`/wounds/${assessment.wound_id}`} className="p-2 text-slate-400 hover:text-slate-700 bg-white rounded-xl border border-slate-200">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Visit #{assessment.visit_number} Assessment</h2>
              <Badge status={assessment.healing_status} />
            </div>
            <p className="text-xs text-slate-500">Recorded on {new Date(assessment.visit_date).toLocaleString()}</p>
          </div>
        </div>

        <button
          onClick={downloadPdf}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-bold px-4 py-2.5 rounded-xl text-xs shadow transition-colors"
        >
          <Download className="w-4 h-4 text-cyan-400" />
          <span>Export Clinical PDF Report</span>
        </button>
      </div>

      {/* Main Visualizations */}
      <MaskViewer
        originalUrl={assessment.original_image_url}
        maskUrl={assessment.mask_image_url}
        overlayUrl={assessment.overlay_image_url}
        confidenceScore={assessment.confidence_score}
        pixelArea={assessment.wound_pixel_area}
        areaMm2={assessment.area_mm2}
        areaCm2={assessment.area_cm2}
        widthMm={assessment.width_mm}
        heightMm={assessment.height_mm}
      />

      {/* Assessment Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="space-y-3">
          <h4 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">
            Calibration & Model Metrics
          </h4>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Linear Calibration Scale</span>
              <span className="font-mono font-bold text-slate-800">{assessment.scale_mm_per_px.toFixed(4)} mm/px</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Target Diameter (px)</span>
              <span className="font-mono font-bold text-slate-800">{assessment.marker_size_px} px</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Known Target Size (mm)</span>
              <span className="font-mono font-bold text-slate-800">{assessment.known_size_mm} mm</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Detection Method</span>
              <span className="font-semibold text-cyan-700">{assessment.is_automatic_calibration ? 'OpenCV Auto' : 'Manual'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">U-Net Model Confidence</span>
              <span className="font-bold text-emerald-600">{(assessment.confidence_score * 100).toFixed(0)}%</span>
            </div>
          </div>
        </Card>

        <Card className="space-y-3">
          <h4 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">
            Clinical Observations
          </h4>
          <p className="text-xs text-slate-600 leading-relaxed italic">
            {assessment.clinician_notes || 'No specific clinical observations recorded for this visit.'}
          </p>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
            <span>Visit Trajectory Change</span>
            <span className="font-bold text-slate-800">
              {assessment.percentage_change !== null ? `${assessment.percentage_change}%` : 'Baseline Visit'}
            </span>
          </div>
        </Card>
      </div>
    </div>
  );
};
