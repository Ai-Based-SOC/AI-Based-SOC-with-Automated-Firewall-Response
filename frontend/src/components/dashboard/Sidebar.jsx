import React from "react";
import { Link } from "react-router-dom";

const sidebarItems = [
  { path: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { path: "/incidents", label: "Incidents", icon: "AlertCircle" },
  { path: "/threat-intelligence", label: "Threat Intelligence", icon: "Search" },
  { path: "/firewall", label: "Firewall", icon: "Shield" },
  { path: "/logs", label: "Logs", icon: "FileText" },
  { path: "/reports", label: "Reports", icon: "BarChart3" },
  { path: "/ai-assistant", label: "AI Assistant", icon: "Brain" },
  { path: "/system-health", label: "System Health", icon: "Settings" },
  { path: "/settings", label: "Settings", icon: "Users" },
];

export function Sidebar() {
  return (
    <nav className="soc-sidebar bg-[#0e1521] min-h-screen border-r border-slate-700">
      <div className="p-6 pt-8 border-b border-slate-700 border-solid">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-600 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8" cy="8" r="2"/>
              <circle cx="16" cy="16" r="2"/>
            </svg>
          </div>
          <span className="text-xl font-bold text-white">AI SOC</span>
        </div>
        <span className="text-slate-500 text-xs mt-2 block">AI Based Security Operations Center</span>
      </div>
      <div className="p-6">
        <nav className="space-y-2">
          {sidebarItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="soc-nav-item flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:text-cyan-400 hover:bg-slate-600 transition-colors"
              style={{ background: item.path === window.location.pathname ? 'rgba(30, 136, 229, 0.15)' : 'transparent' }}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12l2-2m0 0l7-7m-7 7l2 2m2-6l2 2m7-2a4 4 0 11-8 0 4 4 0 018 0 4 4 0 01-8 0"/>
              </svg>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>
      <div className="p-6 border-t border-slate-700">
        <div className="flex items-center gap-3 text-slate-500 text-xs">
          <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="10" cy="10" r="7"/>
            </svg>
          </div>
          <span>admin@soc.local</span>
        </div>
        <div className="mt-3">
          <span className="text-slate-400 text-xs">Role</span>
          <span className="ml-2 text-cyan-400 text-xs font-medium">Admin</span>
        </div>
        <button
          onClick={() => window.location.href = '/api/v1/auth/logout'}
          className="mt-3 w-full flex justify-center py-2 px-4 rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 transition-colors"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}