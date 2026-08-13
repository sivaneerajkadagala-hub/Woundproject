import React from 'react';
import { AlertTriangle, Cpu, Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 sticky top-0 z-10 px-6 flex items-center justify-between shadow-sm">
      {/* Disclaimer Banner */}
      <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-900 px-3 py-1.5 rounded-lg text-xs font-medium">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>
          <b>Decision-Support Tool:</b> Pretrained U-Net segmentation output requires qualified healthcare review.
        </span>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Model Status Pill */}
        <div className="hidden md:flex items-center gap-2 bg-cyan-50 border border-cyan-200 text-cyan-800 px-3 py-1 rounded-full text-xs font-medium">
          <Cpu className="w-3.5 h-3.5 text-cyan-600 animate-pulse" />
          <span>U-Net Pretrained Ready</span>
        </div>

        {/* Notifications */}
        <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyan-500 rounded-full"></span>
        </button>

        {/* User Pill */}
        <div className="flex items-center gap-2 border-l border-slate-200 pl-4">
          <span className="text-xs font-semibold text-slate-700">{user?.full_name}</span>
          <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-bold uppercase">
            {user?.role}
          </span>
        </div>
      </div>
    </header>
  );
};
