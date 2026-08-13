import React, { useState } from 'react';
import { Ruler, RefreshCw, CheckCircle2, Sliders } from 'lucide-react';

interface CalibrationStepProps {
  knownSizeMm: number;
  markerSizePx: number;
  scaleMmPerPx: number;
  isAutomatic: boolean;
  onCalibrationChange: (knownMm: number, markerPx: number) => void;
}

export const CalibrationStep: React.FC<CalibrationStepProps> = ({
  knownSizeMm,
  markerSizePx,
  scaleMmPerPx,
  isAutomatic,
  onCalibrationChange
}) => {
  const [manualMm, setManualMm] = useState<number>(knownSizeMm);
  const [manualPx, setManualPx] = useState<number>(markerSizePx);
  const [isManualMode, setIsManualMode] = useState<boolean>(!isAutomatic);

  const handleApply = () => {
    onCalibrationChange(manualMm, manualPx);
  };

  return (
    <div className="bg-slate-900 text-slate-100 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-cyan-500/20 text-cyan-400 rounded-xl">
            <Ruler className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-white text-base">Calibration Scale Engine</h4>
            <p className="text-xs text-slate-400">Determines linear pixel-to-millimeter ratio</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${
          isAutomatic
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
        }`}>
          {isAutomatic ? 'Auto OpenCV Detected' : 'Manual Calibrated'}
        </span>
      </div>

      {/* Math Banner */}
      <div className="grid grid-cols-3 gap-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 font-mono text-center text-xs">
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-sans">Known Target</span>
          <span className="text-cyan-400 text-base font-bold">{knownSizeMm} mm</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-sans">Image Distance</span>
          <span className="text-white text-base font-bold">{markerSizePx} px</span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase font-sans">Linear Scale</span>
          <span className="text-emerald-400 text-base font-bold">{scaleMmPerPx.toFixed(4)} mm/px</span>
        </div>
      </div>

      {/* Manual Calibration Accordion */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => setIsManualMode(!isManualMode)}
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1.5 transition-colors"
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>{isManualMode ? 'Hide Manual Adjustments' : 'Adjust Marker Size Manually'}</span>
        </button>

        {isManualMode && (
          <div className="mt-3 p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">
                  Real Marker Size (mm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={manualMm}
                  onChange={(e) => setManualMm(parseFloat(e.target.value) || 10.0)}
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">
                  Marker Size in Pixels (px)
                </label>
                <input
                  type="number"
                  step="1"
                  value={manualPx}
                  onChange={(e) => setManualPx(parseFloat(e.target.value) || 100.0)}
                  className="w-full bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-xs focus:ring-1 focus:ring-cyan-500"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={handleApply}
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Update Scale Ratio</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
