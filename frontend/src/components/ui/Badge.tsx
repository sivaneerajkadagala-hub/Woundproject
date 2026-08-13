import React from 'react';

interface BadgeProps {
  status: 'Improving' | 'Stable' | 'Increasing' | 'Baseline' | 'Active' | 'Closed' | 'Attention Required' | string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, className = '' }) => {
  let colorStyle = 'bg-slate-100 text-slate-700 border-slate-200';

  switch (status) {
    case 'Improving':
      colorStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold';
      break;
    case 'Stable':
      colorStyle = 'bg-cyan-50 text-cyan-700 border-cyan-200 font-semibold';
      break;
    case 'Increasing':
    case 'Attention Required':
      colorStyle = 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
      break;
    case 'Active':
      colorStyle = 'bg-blue-50 text-blue-700 border-blue-200 font-semibold';
      break;
    case 'Closed':
      colorStyle = 'bg-slate-100 text-slate-600 border-slate-200';
      break;
    case 'Baseline':
      colorStyle = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs border ${colorStyle} ${className}`}>
      {status}
    </span>
  );
};
