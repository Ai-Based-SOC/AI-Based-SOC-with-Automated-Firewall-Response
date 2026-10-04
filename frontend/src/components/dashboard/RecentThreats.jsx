import React from "react";
import { ShieldAlert, AlertTriangle, Activity, BrainCircuit, Lock, Mail, Zap, Map, Leaf, Music, Fire } from "lucide-react";

const attackTypes = [
  { name: "DoS Attack", icon: ShieldAlert, color: "red-500" },
  { name: "Brute Force", icon: Lock, color: "orange-500" },
  { name: "Suspicious PowerShell", icon: Zap, color: "yellow-500" },
  { name: "Port Scan", icon: Map, color: "lime-500" },
  { name: "Malware Communication", icon: Music, color: "green-500" },
  { name: "Web Attack", icon: Fire, color: "purple-500" },
];

// Map attack types to valid Tailwind classes (no dynamic bg-/{text-} strings)
const severityClasses = {
  "DoS Attack": "bg-red-500/20 text-red-400",
  "Brute Force": "bg-orange-500/20 text-orange-400",
  "Suspicious PowerShell": "bg-yellow-500/20 text-yellow-400",
  "Port Scan": "bg-lime-500/20 text-lime-400",
  "Malware Communication": "bg-green-500/20 text-green-400",
  "Web Attack": "bg-purple-500/20 text-purple-400",
};

export function RecentThreats({ attacks }) {
  return (
    <div>
      <h3 className="soc-heading mb-3">Recent Threats</h3>
      <div className="space-y-3">
        {attackTypes.map((type) => {
          const attackCount = attacks?.filter((a) => a.attack_type === type.name).length || 0;
          const classes = severityClasses[type.name] || "bg-slate-500/20 text-slate-400";
          return (
            <div
              key={type.name}
              className="flex items-center gap-3 px-3 py-2 bg-[#0d1626] rounded-lg border border-slate-700/50 hover:bg-slate-800 transition-colors"
            >
              <div className={`w-3 h-3 rounded-full ${classes.split(" ")[0]}`}></div>
              <span className="text-slate-400 text-sm flex-1">{type.name}</span>
              <span className="text-slate-500 text-xs ml-auto">{attackCount} events</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}