import React from "react";

export function TopBar({ systemStatus, notifications, onThemeChange }) {
  const statusColors = {
    online: "bg-green-600",
    offline: "bg-red-600",
    warning: "bg-orange-600",
    degraded: "bg-yellow-600"
  };

  const statusLabels = {
    online: "System Operational",
    offline: "System Offline",
    warning: "Degraded Performance",
    degraded: "Reduced Capacity"
  };

  return (
    <header className="soc-header bg-[#1a2432] border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="soc-header-title text-xl font-bold text-white">Dashboard</span>
        <span className="soc-header-subtitle text-sm text-slate-400">Real-time security overview and threat intelligence</span>
      </div>
      <div className="flex items-center gap-4">
        <button
          onClick={onThemeChange}
          className="soc-btn soc-btn-icon bg-slate-700 rounded-full p-1.5 hover:bg-slate-600 transition-colors"
          aria-label="Toggle theme"
        >
          <svg className="w-5 h-5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h11l5 5v5a2 2 0 0 1-2 2z"/>
          </svg>
        </button>
        <button
          className="soc-btn soc-btn-icon bg-slate-700 rounded-full p-1.5 hover:bg-slate-600 transition-colors"
          aria-label="Notifications"
        >
          <svg className="w-5 h-5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
            <line x1="9" y1="9" x2="9" y2="9.01"/>
            <line x1="15" y1="9" x2="15" y2="9.01"/>
          </svg>
          <span className="absolute -top-1 right-2 bg-red-600 text-xs text-white rounded-full w-4 h-4 flex items-center justify-center">
            {notifications > 0 ? notifications : ''}
          </span>
        </button>
        <div className="relative">
          <button
            className="soc-btn soc-btn-icon bg-slate-700 rounded-full p-1.5 hover:bg-slate-600 transition-colors"
            aria-label="User profile"
          >
            <svg className="w-5 h-5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M16 21v2a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-2M16 8a4 4 0 0 0-4 4H6a4 4 0 0 0-4 4v2m5-7l-3 3L9 14H6v5a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-2M7 7h2v2H7V7zm5 4h2v2h-2V7z"/>
            </svg>
          </button>
          <div className="absolute right-0 mt-2 w-48 bg-[#1a2432] border border-slate-700 rounded-md p-4 shadow-md text-white text-xs">
            <div className="flex items-center justify-between mb-2">
              <span>admin@soc.local</span>
              <span className="font-medium text-cyan-400">Admin</span>
            </div>
            <div className="flex flex-col space-y-1">
              <button className="w-full py-1 px-3 rounded-md hover:bg-slate-600 transition-colors text-left">
                Profile
              </button>
              <button className="w-full py-1 px-3 rounded-md hover:bg-slate-600 transition-colors text-left">
                Settings
              </button>
              <button className="w-full py-1 px-3 rounded-md hover:bg-red-600/20 text-red-400 transition-colors text-left">
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}