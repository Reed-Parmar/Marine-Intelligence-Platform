import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  Map as MapIcon, 
  Waves, 
  Fish, 
  Dna, 
  Microscope, 
  Cpu, 
  AlertTriangle, 
  ChevronLeft, 
  ChevronRight, 
  ShieldCheck,
  Compass,
  Layers
} from 'lucide-react';
import { Badge } from '../ui/Badge';

export const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navItems = [
    { to: '/', label: 'Command Center', icon: LayoutDashboard, exact: true },
    { to: '/data', label: 'Data Engine', icon: Database, badge: 'TXT/CSV' },
    { to: '/map', label: 'Marine Research Map', icon: MapIcon, highlight: true },
    { to: '/ocean', label: 'Ocean Explorer', icon: Waves },
    { to: '/fisheries', label: 'Fisheries Explorer', icon: Fish },
    { to: '/species', label: 'Species Explorer', icon: Compass },
    { to: '/edna', label: 'eDNA Explorer', icon: Dna, badge: '12S/COI' },
    { to: '/analysis', label: 'Scientific Analysis', icon: Microscope },
    { to: '/ai-insights', label: 'AI Insights', icon: Cpu, badge: 'ML' },
    { to: '/alerts', label: 'Alerts & Hazards', icon: AlertTriangle, alertCount: 3 },
  ];

  return (
    <aside
      className={`relative flex flex-col border-r border-marine-800 bg-marine-950/95 backdrop-blur-xl transition-all duration-300 z-30 ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between px-4 py-5 border-b border-marine-800/80">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-ocean-cyan via-blue-600 to-teal-400 p-[1.5px] flex-shrink-0 shadow-glow-cyan">
            <div className="w-full h-full bg-marine-950 rounded-[10px] flex items-center justify-center">
              <Waves className="w-5 h-5 text-ocean-cyan animate-pulse-subtle" />
            </div>
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-bold tracking-wider text-white uppercase flex items-center gap-1.5 truncate">
                CMLRE
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-ocean-cyan/20 text-ocean-cyan border border-ocean-cyan/30">
                  v2.4
                </span>
              </h1>
              <p className="text-[10px] text-slate-400 truncate">Marine Intelligence Platform</p>
            </div>
          )}
        </div>

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-marine-800/80 transition-colors hidden md:flex items-center justify-center"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Ministry / Org Subtitle */}
      {!isCollapsed && (
        <div className="px-4 py-2 bg-marine-900/40 border-b border-marine-800/50 flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-ocean-teal flex-shrink-0" />
          <span className="text-[10px] font-medium text-slate-300 truncate">
            Ministry of Earth Sciences (MoES)
          </span>
        </div>
      )}

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group relative ${
                  isActive
                    ? 'bg-gradient-to-r from-ocean-cyan/20 to-blue-600/10 text-ocean-cyan border border-ocean-cyan/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-marine-900/80'
                }`
              }
              title={isCollapsed ? item.label : undefined}
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition-colors ${
                      isActive ? 'text-ocean-cyan' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  {!isCollapsed && (
                    <span className="truncate flex-1 tracking-wide">{item.label}</span>
                  )}
                  {!isCollapsed && item.badge && (
                    <Badge variant="cyan" size="sm" className="ml-auto">
                      {item.badge}
                    </Badge>
                  )}
                  {!isCollapsed && item.alertCount && (
                    <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-ocean-coral text-white animate-pulse">
                      {item.alertCount}
                    </span>
                  )}
                  {isCollapsed && item.alertCount && (
                    <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-ocean-coral animate-ping" />
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Spatial Node Info */}
      <div className="p-3 border-t border-marine-800/80">
        <div className={`p-2.5 rounded-xl bg-marine-900/60 border border-marine-800 ${isCollapsed ? 'text-center' : ''}`}>
          <div className="flex items-center gap-2 text-slate-300">
            <Layers className="w-3.5 h-3.5 text-ocean-teal flex-shrink-0" />
            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="text-[11px] font-semibold text-white truncate">Arabian Sea & BoB Node</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] text-slate-400 font-mono">PostGIS Synced</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};
