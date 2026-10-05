import { useCallback, useEffect, useState } from "react";
import { Activity, Cpu, HardDrive, MemoryStick, Network } from "lucide-react";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import { healthApi } from "../services/api";

const services = [
  "Backend API",
  "Database",
  "Firewall Service",
  "WebSocket",
  "AI/ML Models",
];

export default function SystemHealthPage({ profile, onLogout }) {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const response = await healthApi();
      setHealth(response.data);
      setError("");
    } catch {
      setError("System health service is unavailable.");
    }
  }, []);

  useEffect(() => {
    load();

    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load]);

  const metrics = health?.metrics || {};

  const cards = [
    {
      label: "CPU Usage",
      value: metrics.cpu ?? "--",
      icon: Cpu,
      color: "text-cyan-300",
    },
    {
      label: "Memory Usage",
      value: metrics.memory ?? "--",
      icon: MemoryStick,
      color: "text-purple-300",
    },
    {
      label: "Disk Usage",
      value: metrics.disk ?? "--",
      icon: HardDrive,
      color: "text-green-300",
    },
    {
      label: "Network Usage",
      value: metrics.network ?? "--",
      icon: Network,
      color: "text-orange-300",
    },
  ];

  return (
    <PageShell
      title="System Health"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1600px] space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">System Health</h2>
            <p className="text-sm text-slate-400">
              Monitor system performance and service status
            </p>
          </div>

          <span className="rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-2 text-sm text-green-300">
            ● {health?.status || "Checking"}
          </span>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {cards.map(({ label, value, icon: Icon, color }) => (
            <Panel key={label}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase text-slate-500">{label}</p>
                  <p className={`mt-2 text-3xl font-bold ${color}`}>
                    {value}
                  </p>
                </div>

                <Icon className={color} />
              </div>
            </Panel>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Panel title="Service Status" icon={<Activity size={16} />}>
            <div className="space-y-3">
              {services.map((service) => (
                <div
                  key={service}
                  className="flex items-center justify-between border-b border-cyan-950 pb-3 last:border-0"
                >
                  <span className="text-sm text-slate-300">{service}</span>
                  <span className="text-xs text-green-300">
                    ● Operational
                  </span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Resource Usage">
            <div className="flex h-64 items-end gap-3 rounded-lg border border-cyan-950 bg-[#041326] p-4">
              {[35, 44, 39, 57, 48, 68, 55, 72, 61, 78].map(
                (height, index) => (
                  <div
                    key={index}
                    className="flex-1 rounded-t bg-gradient-to-t from-cyan-600 to-cyan-300"
                    style={{ height: `${height}%` }}
                  />
                )
              )}
            </div>
          </Panel>
        </div>
      </div>
    </PageShell>
  );
}