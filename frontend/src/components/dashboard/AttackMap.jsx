import React from "react";
import { MapPin, TrendingUp, Shield, AlertCircle } from "lucide-react";

export function AttackMap({ attacks, onMarkerClick }) {
  if (!attacks || attacks.length === 0) {
    return (
      <div className="soc-panel h-[400px] border-t border-border bg-card">
        <div className="flex flex-col items-center justify-center text-slate-500 h-full">
          <svg className="w-12 h-12 mb-3 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-1.73-1H2a2 2 0 0 0-1 1.73l7 4a2 2 0 0 0 1 1.73v8z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22" x2="12.01" y2="22"/>
            <polyline points="10.94 4.96 12 12.01 13.07 4.96"/>
          </svg>
          <p>No active attacks</p>
          <p className="text-xs mt-1">Attack data will appear here when threats are detected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[420px]">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="soc-heading mb-3">Live Attack Map</h3>
          <div className="soc-panel h-[360px] border-t border-border bg-card relative">
            <div className="h-full relative bg-slate-900/50 rounded overflow-hidden">
              {attacks.map((attack, index) => (
                <div
                  key={index}
                  className="absolute p-2 cursor-pointer transition-all duration-300 hover:opacity-80"
                  style={{
                    left: Math.random() * 100,
                    top: Math.random() * 80,
                    borderRadius: "50%"
                  }}
                  onClick={() => onMarkerClick && onMarkerClick(attack)}
                >
                  <div className="w-6 h-6 rounded-full bg-cyan-500 border border-slate-700/50 flex items-center justify-center text-xs font-bold">
                    {attack.ip?.substring(0, 2) || "??"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <h3 className="soc-heading mb-3">Attacker Details</h3>
          {onMarkerClick && (
            <div className="space-y-2">
              {attacks.map((attack) => (
                <div
                  key={attack.ip}
                  className="p-2 px-3 bg-[#0d1626] rounded-lg border border-slate-700/50 hover:bg-slate-800 cursor-pointer transition-colors"
                  onClick={() => onMarkerClick(attack)}
                >
                  <span className="font-medium text-cyan-400 w-20 inline-block">{attack.ip || 'N/A'}</span>
                  <span>{attack.severity || 'N/A'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 text-slate-500 text-center">
              Click on an attack to see details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}