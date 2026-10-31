import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Radio,
  Brain,
  BarChart3,
  Users,
  Database,
  Cpu,
  Server,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { systemApi } from '../services/api';
import { SystemStatus } from '../types';

const navItems = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'Live Monitoring', path: '/live', icon: Activity },
  { name: 'EEG Explorer', path: '/explorer', icon: Radio },
  { name: 'Brain-State ML', path: '/classification', icon: Brain },
  { name: 'Signal Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Participants', path: '/participants', icon: Users },
  { name: 'Hive Analytics', path: '/hive', icon: Database },
  { name: 'Model Evaluation', path: '/model', icon: Cpu },
  { name: 'System Monitoring', path: '/system', icon: Server },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [sysStatus, setSysStatus] = useState<SystemStatus | null>(null);
  const location = useLocation();

  useEffect(() => {
    const fetchStatus = () => {
      systemApi.getStatus()
        .then(setSysStatus)
        .catch(() => setSysStatus(null));
    };
    fetchStatus();
    const timer = setInterval(fetchStatus, 5000);
    return () => clearInterval(timer);
  }, []);

  const getServiceStatus = (key: 'kafka' | 'hive' | 'hdfs' | 'spark') => {
    return sysStatus?.services[key]?.status === 'connected';
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 antialiased overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`bg-white border-r border-slate-200 flex flex-col justify-between transition-all duration-300 z-30 shadow-sm ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        <div>
          {/* Brand Logo & Name */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white font-bold text-xl shadow-md flex-shrink-0">
                ⚡
              </div>
              {!collapsed && (
                <div className="flex flex-col">
                  <span className="font-bold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
                    NeuroStream
                    <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                      v1.0
                    </span>
                  </span>
                  <span className="text-xs text-slate-500 truncate">Distributed EEG Platform</span>
                </div>
              )}
            </div>
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            >
              {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-140px)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-3 py-2.5 rounded-lg font-medium text-sm transition-all group ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                  title={collapsed ? item.name : undefined}
                >
                  <Icon
                    size={20}
                    className={`flex-shrink-0 transition-colors ${
                      isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  {!collapsed && <span className="ml-3 truncate">{item.name}</span>}
                  {isActive && !collapsed && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-600" />
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer with Academic Badge */}
        {!collapsed ? (
          <div className="p-4 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
              <ShieldAlert size={14} className="text-amber-500 flex-shrink-0" />
              <span className="font-medium text-slate-700">Academic MicroProject</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              PhysioNet EEGMMIDB Motor Movement / Imagery Dataset (64-Ch, 160Hz).
            </p>
          </div>
        ) : (
          <div className="p-3 border-t border-slate-100 flex justify-center" title="Academic MicroProject">
            <ShieldAlert size={18} className="text-amber-500" />
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between z-20 shadow-xs">
          <div className="flex items-center space-x-3">
            <h1 className="text-lg font-semibold text-slate-900">
              {navItems.find((n) => n.path === location.pathname)?.name || 'Dashboard'}
            </h1>
            <span className="text-slate-300">|</span>
            <span className="text-xs text-slate-500 font-mono hidden md:inline">
              Apache Kafka &bull; Spark Streaming &bull; Hadoop HDFS &bull; Apache Hive
            </span>
          </div>

          {/* Persistent Distributed Systems Health Indicators */}
          <div className="flex items-center space-x-2">
            {[
              { name: 'Kafka', key: 'kafka' as const },
              { name: 'Spark', key: 'spark' as const },
              { name: 'HDFS', key: 'hdfs' as const },
              { name: 'Hive', key: 'hive' as const },
            ].map((svc) => {
              const ok = getServiceStatus(svc.key);
              return (
                <div
                  key={svc.name}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                    ok
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border-rose-200'
                  }`}
                  title={`${svc.name}: ${ok ? 'Online' : 'Disconnected'}`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      ok ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                    }`}
                  />
                  <span>{svc.name}</span>
                </div>
              );
            })}
          </div>
        </header>

        {/* Page Body Viewport */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
