import React, { useState } from 'react';
import { Eye, ShieldAlert, Cpu, Sparkles, Layers, Image as ImageIcon } from 'lucide-react';

interface MaskViewerProps {
  originalUrl: string;
  maskUrl: string;
  overlayUrl: string;
  confidenceScore: number;
  pixelArea: number;
  areaMm2: number;
  areaCm2: number;
  widthMm: number;
  heightMm: number;
}

export const MaskViewer: React.FC<MaskViewerProps> = ({
  originalUrl,
  maskUrl,
  overlayUrl,
  confidenceScore,
  pixelArea,
  areaMm2,
  areaCm2,
  widthMm,
  heightMm
}) => {
  const [activeTab, setActiveTab] = useState<'overlay' | 'original' | 'mask'>('overlay');

  const getCurrentImage = () => {
    switch (activeTab) {
      case 'original':
        return originalUrl;
      case 'mask':
        return maskUrl;
      case 'overlay':
      default:
        return overlayUrl;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-lg space-y-0">
      {/* Header & Mode Selector */}
      <div className="p-4 bg-slate-900 text-white flex flex-wrap items-center justify-between gap-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-cyan-400" />
          <span className="font-bold text-sm tracking-tight">U-Net Segmentation Result</span>
          <span className="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-0.5 rounded-full font-mono border border-cyan-500/30">
            {(confidenceScore * 100).toFixed(0)}% Confidence
          </span>
        </div>

        {/* View Tabs */}
        <div className="flex bg-slate-800 p-1 rounded-xl gap-1 border border-slate-700">
          <button
            type="button"
            onClick={() => setActiveTab('original')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'original'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Original</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('mask')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'mask'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Binary Mask</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('overlay')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'overlay'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Highlight Overlay</span>
          </button>
        </div>
      </div>

      {/* Main Image Display Box */}
      <div className="relative bg-slate-950 min-h-[380px] flex items-center justify-center p-4">
        <img
          src={getCurrentImage()}
          alt={`Wound view ${activeTab}`}
          className="max-h-[420px] object-contain rounded-xl shadow-2xl border border-slate-800"
        />

        {/* View Badge overlay */}
        <div className="absolute top-6 left-6 bg-slate-900/80 backdrop-blur-md text-white text-xs px-3 py-1 rounded-lg border border-slate-700 uppercase tracking-wider font-semibold font-mono">
          View Mode: {activeTab}
        </div>
      </div>

      {/* Surface Area Measurement Cards */}
      <div className="p-6 bg-slate-50 border-t border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Wound Surface Area</span>
          <span className="text-2xl font-extrabold text-cyan-700">{areaMm2} mm²</span>
          <span className="text-xs text-slate-400 block mt-0.5 font-medium">{areaCm2} cm²</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Bounding Dimensions</span>
          <span className="text-xl font-bold text-slate-800">{widthMm} x {heightMm}</span>
          <span className="text-xs text-slate-400 block mt-0.5 font-medium">Millimeters (W x H)</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Mask Surface Pixels</span>
          <span className="text-xl font-bold text-slate-800">{pixelArea.toLocaleString()} px²</span>
          <span className="text-xs text-slate-400 block mt-0.5 font-medium">Segmented Region</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Model Confidence</span>
          <span className="text-xl font-bold text-emerald-600">{(confidenceScore * 100).toFixed(0)}%</span>
          <span className="text-xs text-slate-400 block mt-0.5 font-medium">U-Net Pretrained</span>
        </div>
      </div>
    </div>
  );
};
