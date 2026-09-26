import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  PlusCircle, 
  GitCompare, 
  FileText, 
  Bot, 
  LogOut, 
  Activity,
  ShieldCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { logout, user } = useAuth();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Patients', path: '/patients', icon: Users },
    { name: 'New Assessment', path: '/assessment/new', icon: PlusCircle },
    { name: 'Compare Visits', path: '/compare', icon: GitCompare },
    { name: 'Clinical Reports', path: '/reports', icon: FileText },
    { name: 'AI Assistant', path: '/assistant', icon: Bot },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen sticky top-0 border-r border-slate-800 shadow-xl z-20">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="bg-gradient-to-tr from-cyan-500 to-teal-400 p-2.5 rounded-xl shadow-lg shadow-cyan-500/20 text-white">
          <Activity className="w-6 h-6" />
        </div>
        <div>
          <h1 className="font-bold text-white text-lg tracking-tight flex items-center gap-1.5">
            WoundAI <span className="bg-cyan-500/20 text-cyan-400 text-xs px-2 py-0.5 rounded-full font-semibold">PRO</span>
          </h1>
          <p className="text-xs text-slate-400">Segmentation & Healing</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Security & Prototype Disclaimer Box */}
      <div className="px-4 py-3 mx-3 mb-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-xs text-slate-400 space-y-1">
        <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Decision Support</span>
        </div>
        <p className="text-[11px] leading-tight text-slate-400">
          CV color segmentation prototype. Synthetic demo data only.
        </p>
      </div>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-cyan-900 text-cyan-300 font-bold flex items-center justify-center text-sm border border-cyan-700">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="truncate">
            <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Clinician'}</p>
            <p className="text-[10px] text-cyan-400 capitalize font-medium">{user?.role || 'Clinician'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          title="Logout"
          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
