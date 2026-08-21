import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  LogOut, 
  UserCheck, 
  Sparkles, 
  ShieldAlert, 
  Activity, 
  Globe
} from 'lucide-react';
import { Badge } from '../ui/Badge';

export const Header: React.FC = () => {
  const { user, logout, switchDemoRole } = useAuth();

  return (
    <header className="h-16 border-b border-marine-800 bg-marine-950/80 backdrop-blur-xl px-6 flex items-center justify-between z-20">
      {/* Sector Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-marine-900/80 border border-marine-700/60 text-xs text-slate-300">
          <Globe className="w-3.5 h-3.5 text-ocean-cyan animate-spin-slow" />
          <span className="font-semibold text-white">Indian EEZ & Adjacent Oceanic Sector</span>
          <span className="text-[10px] text-slate-400 font-mono">EPSG:4326</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-ocean-teal/10 border border-ocean-teal/30 text-ocean-teal text-xs">
          <Activity className="w-3 h-3 animate-pulse" />
          <span className="font-mono text-[11px]">FastAPI Ingestion Online</span>
        </div>
      </div>

      {/* User Controls & Demo Switcher */}
      <div className="flex items-center gap-4">
        {/* Quick Demo Role Switcher for Hackathon Demo */}
        <div className="hidden sm:flex items-center gap-1.5 p-1 rounded-lg bg-marine-900 border border-marine-800 text-xs">
          <span className="text-[11px] text-slate-400 px-2">Demo Role:</span>
          <button
            onClick={() => switchDemoRole('user')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
              user?.role === 'user'
                ? 'bg-ocean-cyan text-marine-950 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Scientist
          </button>
          <button
            onClick={() => switchDemoRole('admin')}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
              user?.role === 'admin'
                ? 'bg-ocean-amber text-marine-950 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Admin (MoES)
          </button>
        </div>

        {/* User Profile Pill */}
        <div className="flex items-center gap-3 pl-3 border-l border-marine-800">
          <img
            src={user?.avatarUrl || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'}
            alt="Profile"
            className="w-8 h-8 rounded-full border border-ocean-cyan/60 object-cover ring-2 ring-marine-800"
          />
          <div className="hidden md:block text-left">
            <p className="text-xs font-semibold text-white leading-none truncate max-w-[140px]">
              {user?.fullName || 'Dr. Ananya Nair'}
            </p>
            <div className="flex items-center gap-1.5 mt-1">
              <Badge variant={user?.role === 'admin' ? 'amber' : 'cyan'} size="sm">
                {user?.role === 'admin' ? 'MoES Admin' : 'Marine Scientist'}
              </Badge>
            </div>
          </div>

          <button
            onClick={() => logout()}
            className="p-2 rounded-lg text-slate-400 hover:text-ocean-coral hover:bg-marine-900 transition-colors"
            title="Logout from CMLRE session"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
