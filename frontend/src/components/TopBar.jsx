import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function TopBar({ systemStatus, notifications }) {
  const navigate = useNavigate();
  const { profile } = useAuth();

  const handleLogout = () => {
    localStorage.removeItem("soc_token");
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <header className="soc-topbar">
      <div className="soc-brand">
        <span>AI SOC</span>
      </div>

      <nav className="nav-breadcrumbs">
        <span>Home</span>
        <span>/ Dashboard</span>
      </nav>

      <div className="topbar-right">
        <div className="status-dot {systemStatus === 'online' && 'dot-green'}" />
        <span className="ml-3 text-slate-400 text-xs">System: {systemStatus}</span>

        <div className="notifications-dropdown relative cursor-pointer">
          <button className="flex items-center gap-2 px-3 py-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-400">
            <i className="bell-icon" /> {notifications > 0 ? <span className="notification-badge">{notifications}</span> : null}
          </button>

          {notifications > 0 && (
            <div className="absolute right-0 top-full mt-2 w-56 bg-slate-900 border border-slate-700 rounded-md p-4 max-h-80 overflow-y-auto">
              <p className="text-slate-500 text-sm mb-3">Recent notifications</p>
              <ul className="space-y-1 text-xs text-slate-300">
                <li>New threat detected</li>
                <li>Firewall rule updated</li>
                <li>Login attempt blocked</li>
              </ul>
            </div>
          )}
        </div>

        <div className="ml-4">
          <button onClick={handleLogout} className="px-4 py-2 rounded bg-slate-700 hover:bg-slate-600 text-sm">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}