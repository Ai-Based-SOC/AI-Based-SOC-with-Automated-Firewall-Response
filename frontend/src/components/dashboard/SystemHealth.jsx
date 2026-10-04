import React, { useState, useEffect } from "react";
import { Shield, Zap, Leaf, Mail, Cloud, Server, Database, Monitor, Network, Alarm, Settings, Palette, Cpu, Memory, Disk, Folder, CloudDownload, CloudUpload, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { healthApi } from "../../services/api";

const services = [
  { name: "CPU", icon: Cpu, id: "cpu" },
  { name: "Memory", icon: Memory, id: "memory" },
  { name: "Disk", icon: Disk, id: "disk" },
  { name: "Network", icon: Network, id: "network" },
  { name: "Database", icon: Database, id: "database" },
  { name: "WebSocket", icon: Monitor, id: "websocket" },
  { name: "Firewall Service", icon: Shield, id: "firewall" },
  { name: "Event Collector", icon: Folder, id: "event" },
  { name: "ML Engine", icon: Palette, id: "ml" },
];

// Map health status to valid explicit Tailwind classes (no dynamic bg-/{text-} strings)
const healthClassMap = {
  operational: {
    bg: "bg-green-600/20",
    border: "border-green-600/30",
    text: "text-green-400"
  },
  warning: {
    bg: "bg-orange-600/20",
    border: "border-orange-600/30",
    text: "text-orange-400"
  },
  degraded: {
    bg: "bg-yellow-600/20",
    border: "border-yellow-600/30",
    text: "text-yellow-400"
  },
  offline: {
    bg: "bg-red-600/20",
    border: "border-red-600/30",
    text: "text-red-400"
  }
};

export function SystemHealth({ servicesData }) {
  const [healthStatus, setHealthStatus] = useState({});

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const { data } = await healthApi();
        setHealthStatus(data || {});
      } catch (error) {
        console.error("Failed to fetch system health:", error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h3 className="soc-heading mb-3">System Health</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {services.map((service) => {
          const serviceKey = service.id;
          const currentHealth = healthStatus[serviceKey] || "offline";
          const healthLabels = {
            operational: { text: "Operational", bg: "bg-green-600/20", border: "bg-green-600/30", color: "green-400" },
            warning: { text: "Warning", bg: "bg-orange-600/20", border: "bg-orange-600/30", color: "orange-400" },
            degraded: { text: "Degraded", bg: "bg-yellow-600/20", border: "bg-yellow-600/30", color: "yellow-400" },
            offline: { text: "Offline", bg: "bg-red-600/20", border: "bg-red-600/30", color: "red-400" }
          };
          const health = healthLabels[currentHealth] || healthLabels.offline;

          return (
            <div
              key={service.name}
              className="soc-panel bg-[#0d1626] rounded-lg border border-slate-700/50 p-3 text-center transition-colors hover:border-cyan-500/30"
            >
              <div className="w-6 h-6 mx-auto mb-2 rounded-lg {health.bg}">
                <svg className="w-3 h-3 text-{health.color}" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  {service.icon === Shield && <path d="M12 2v4m0 12v-4m6-8a4 4 0 11-8 0 4 4 0 018 0m5 1a2 2 0 01-2 2v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4a2 2 0 01-2-2m2 6a2 2 0 10-4 0 2 2 0 004 0zM2 4a2 2 0 012-2h2.3a2 2 0 011 1.73m-3.39 3.67A2.32 2.32 0 016.34 8s1.58.67 2.32 1.33m-2.32-1.33A2.32 2.32 0 012 6.34s.67 1.58 1.33 2.32m7.66 0c.71 0 1.33.28 1.84.75l.06.06a2.32 2.32 0 01-1.23 1.95l-.45.23a1.71 1.71 0 01-.4.83h.42a2.24 2.24 0 012.06 0l.42-.23a1.71 1.71 0 01.4-.83l.06-.06a2.32 2.32 0 011.17-1.13l.06-.06c.5-.22 1.08-.41 1.66-.62a12.32 12.32 0 00.6-2.45m-.44-3.32a12.32 12.32 0 00-.6 2.45c.5.22 1.08.41 1.66.62l.06.06a2.32 2.32 0 011.17 1.13l.06.06c.5.22 1.08.41 1.66.62a4.33 4.33 0 011.83 1.12l.06.06c.5.22 1.08.41 1.66.62a4.5 4.5 0 011.98-.02m.67 0c.71 0 1.33.28 1.84.75l.06.06a2.32 2.32 0 01-1.23 1.95l-.45.23a1.71 1.71 0 01-.4.83h.42a2.24 2.24 0 012.06 0l.42-.23a1.71 1.71 0 01.4-.83l.06-.06a2.32 2.32 0 011.17-1.13l.06-.06c.5-.22 1.08-.41 1.66-.62a12.32 12.32 0 00.6-2.45m-.44-3.32a12.32 12.32 0 00-.6 2.45c.5.22 1.08.41 1.66.62l.06.06a2.32 2.32 0 011.17 1.13l.06.06c.5.22 1.08.41 1.66.62a4.33 4.33 0 011.83 1.12l.06.06c.5.22 1.08.41 1.66.62a4.5 4.5 0 011.98-.02 "/>}
                </svg>
              </div>
              <h4 className="font-medium text-white mb-1">{service.name}</h4>
              <p className={currentHealth === "operational" ? "text-green-400" : currentHealth === "warning" ? "text-orange-400" : currentHealth === "degraded" ? "text-yellow-400" : "text-red-400"} text-sm font-medium>
                {health.text}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}