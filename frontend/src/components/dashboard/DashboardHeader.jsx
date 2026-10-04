import React from "react";
import { useState, useEffect } from "react";

export function DashboardHeader() {
  const [dateTime, setDateTime] = useState(new Date().toLocaleString());
  useEffect(() => {
    const timer = setInterval(() => setDateTime(new Date().toLocaleString()), 60000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="dashboard-header bg-[#1a2432] border-b border-slate-700 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Dashboard
          </h1>
          <p className="mt-1 text-slate-400 text-sm">
            Real-time security overview and threat intelligence
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select className="soc-select bg-slate-700 border border-slate-600 rounded-md px-3 py-1.5 text-white text-sm focus:outline-none focus:border-cyan-500">
            <option>Last 24h</option>
            <option>Last 7d</option>
            <option>Last 30d</option>
          </select>
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12a1 1 0 0 1 1-1h13a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-3l-3 3v5a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1h3l3-3v-5a1 1 0 0 1 1-1z"/>
            </svg>
            <select className="bg-transparent border-0 w-24 pl-7 text-white appearance-none cursor-pointer">
              <option>Range</option>
              <option>Last 24h</option>
              <option>Last 7d</option>
              <option>Last 30d</option>
            </select>
            <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12a1 1 0 0 1 1-1h13a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1h-3l-3 3v5a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1h3l3-3v-5a1 1 0 0 1 1-1z"/>
            </svg>
          </div>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="soc-btn soc-btn-sm bg-cyan-600 text-black px-3 py-1 rounded-md text-sm hover:bg-cyan-500 transition-colors">
          Live
        </button>
        <button className="soc-btn soc-btn-sm bg-slate-600 text-white px-3 py-1 rounded-md text-sm hover:bg-slate-500 transition-colors">
          24h
        </button>
        <button className="soc-btn soc-btn-sm bg-slate-600 text-white px-3 py-1 rounded-md text-sm hover:bg-slate-500 transition-colors">
          7d
        </button>
      </div>
    </header>
  );
}