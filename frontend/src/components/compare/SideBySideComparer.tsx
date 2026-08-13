import React from 'react';
import { HealingHistoryPoint } from '../../types';
import { Badge } from '../ui/Badge';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

interface SideBySideComparerProps {
  visitA: HealingHistoryPoint;
  visitB: HealingHistoryPoint;
}

export const SideBySideComparer: React.FC<SideBySideComparerProps> = ({ visitA, visitB }) => {
  const areaA = visitA.area_mm2;
  const areaB = visitB.area_mm2;

  const areaDiff = areaB - areaA;
  const pctDiff = areaA > 0 ? ((areaDiff / areaA) * 100).toFixed(1) : '0';
  const isReduction = areaDiff < 0;

  return (
    <div className="space-y-6">
      {/* Header comparison summary pill */}
      <div className="bg-slate-900 text-white p-5 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-semibold text-slate-400">Longitudinal Area Comparison</h4>
          <p className="text-xl font-extrabold text-white">
            Visit #{visitA.visit_number} vs Visit #{visitB.visit_number}
          </p>
        </div>

        <div className="flex items-center gap-4 bg-slate-950 px-5 py-3 rounded-xl border border-slate-800">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Net Area Reduction</span>
            <div className="flex items-center gap-1.5">
              {isReduction ? (
                <ArrowDownRight className="w-5 h-5 text-emerald-400" />
              ) : areaDiff > 0 ? (
                <ArrowUpRight className="w-5 h-5 text-rose-400" />
              ) : (
                <Minus className="w-5 h-5 text-cyan-400" />
              )}
              <span className={`text-xl font-bold ${isReduction ? 'text-emerald-400' : 'text-rose-400'}`}>
                {Math.abs(Number(pctDiff))}% ({Math.abs(areaDiff).toFixed(1)} mm²)
              </span>
            </div>
          </div>
          <Badge status={isReduction ? 'Improving' : areaDiff > 0 ? 'Increasing' : 'Stable'} />
        </div>
      </div>

      {/* Side by side cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Visit A */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-xs text-cyan-600 font-bold uppercase tracking-wider">Earlier Assessment</span>
              <h5 className="font-extrabold text-slate-800 text-lg">Visit #{visitA.visit_number}</h5>
              <p className="text-xs text-slate-400">{new Date(visitA.visit_date).toLocaleDateString()}</p>
            </div>
            <Badge status={visitA.healing_status} />
          </div>

          <div className="bg-slate-950 rounded-xl overflow-hidden min-h-[220px] flex items-center justify-center">
            {visitA.overlay_image_url ? (
              <img src={visitA.overlay_image_url} alt={`Visit ${visitA.visit_number}`} className="max-h-56 object-contain" />
            ) : (
              <div className="text-slate-500 text-xs">No Image Available</div>
            )}
          </div>

          <div className="bg-slate-50 p-4 rounded-xl space-y-1">
            <span className="text-xs text-slate-500 font-semibold block uppercase">Surface Area</span>
            <span className="text-2xl font-bold text-slate-800">{visitA.area_mm2} mm²</span>
            <span className="text-xs text-slate-400 block">({visitA.area_cm2} cm²)</span>
          </div>
        </div>

        {/* Visit B */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-xs text-cyan-600 font-bold uppercase tracking-wider">Follow-up Assessment</span>
              <h5 className="font-extrabold text-slate-800 text-lg">Visit #{visitB.visit_number}</h5>
              <p className="text-xs text-slate-400">{new Date(visitB.visit_date).toLocaleDateString()}</p>
            </div>
            <Badge status={visitB.healing_status} />
          </div>

          <div className="bg-slate-950 rounded-xl overflow-hidden min-h-[220px] flex items-center justify-center">
            {visitB.overlay_image_url ? (
              <img src={visitB.overlay_image_url} alt={`Visit ${visitB.visit_number}`} className="max-h-56 object-contain" />
            ) : (
              <div className="text-slate-500 text-xs">No Image Available</div>
            )}
          </div>

          <div className="bg-slate-50 p-4 rounded-xl space-y-1">
            <span className="text-xs text-slate-500 font-semibold block uppercase">Surface Area</span>
            <span className="text-2xl font-bold text-slate-800">{visitB.area_mm2} mm²</span>
            <span className="text-xs text-slate-400 block">({visitB.area_cm2} cm²)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
