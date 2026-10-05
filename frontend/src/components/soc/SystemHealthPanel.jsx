import {
  Activity,
  CheckCircle2,
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  Network,
  Radio,
  Server,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";

function normalizeMetric(value) {
  if (value === undefined || value === null || value === "") {
    return "--";
  }

  return String(value);
}

function getStatusClass(status) {
  const value = String(status || "").toLowerCase();

  if (
    value.includes("operational") ||
    value.includes("online") ||
    value.includes("healthy") ||
    value.includes("connected") ||
    value.includes("ready")
  ) {
    return "text-green-300";
  }

  if (
    value.includes("degraded") ||
    value.includes("waiting") ||
    value.includes("polling")
  ) {
    return "text-yellow-300";
  }

  if (
    value.includes("offline") ||
    value.includes("error") ||
    value.includes("failed") ||
    value.includes("unavailable")
  ) {
    return "text-red-300";
  }

  return "text-slate-400";
}

function getStatusIcon(status) {
  const value = String(status || "").toLowerCase();

  if (
    value.includes("operational") ||
    value.includes("online") ||
    value.includes("healthy") ||
    value.includes("connected") ||
    value.includes("ready")
  ) {
    return <CheckCircle2 size={13} />;
  }

  if (
    value.includes("degraded") ||
    value.includes("waiting") ||
    value.includes("polling")
  ) {
    return <TriangleAlert size={13} />;
  }

  return <TriangleAlert size={13} />;
}

function MetricCard({
  label,
  value,
  icon: Icon,
  color,
}) {
  return (
    <div className="rounded-lg border border-cyan-950 bg-[#041326] p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] uppercase tracking-wider text-slate-500">
          {label}
        </p>

        <Icon size={14} className={color} />
      </div>

      <p className={`mt-2 text-xl font-bold ${color}`}>
        {value}
      </p>
    </div>
  );
}

function defaultServices({
  apiHealthy,
  wsConnected,
}) {
  return [
    {
      name: "Backend API",
      status: apiHealthy ? "Operational" : "Unavailable",
    },
    {
      name: "Database",
      status: "Operational",
    },
    {
      name: "Firewall Service",
      status: "Operational",
    },
    {
      name: "WebSocket",
      status: wsConnected ? "Operational" : "Polling",
    },
    {
      name: "AI/ML Models",
      status: "Operational",
    },
  ];
}

export default function SystemHealthPanel({
  attacks = [],
  apiHealthy = false,
  wsConnected = false,
  health = null,
}) {
  const metrics = health?.metrics || {};

  const overallStatus =
    health?.status ||
    (apiHealthy ? "Operational" : "Unavailable");

  const services =
    Array.isArray(health?.services) && health.services.length
      ? health.services
      : defaultServices({
          apiHealthy,
          wsConnected,
        });

  const serviceCount = services.length;
  const operationalCount = services.filter((service) => {
    const status = String(service?.status || "").toLowerCase();

    return (
      status.includes("operational") ||
      status.includes("online") ||
      status.includes("healthy") ||
      status.includes("connected") ||
      status.includes("ready")
    );
  }).length;

  const updatedAt = health?.updated_at
    ? new Date(health.updated_at).toLocaleTimeString()
    : "Waiting for update";

  return (
    <section className="overflow-hidden rounded-xl border border-cyan-900/70 bg-[#071426] shadow-[0_0_18px_rgba(0,120,255,0.08)]">
      <div className="flex items-center justify-between border-b border-cyan-900/70 px-4 py-3">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-cyan-300" />

          <h2 className="text-sm font-semibold text-white">
            System Health
          </h2>
        </div>

        <span
          className={`flex items-center gap-1 text-[10px] font-semibold ${getStatusClass(
            overallStatus
          )}`}
        >
          {getStatusIcon(overallStatus)}
          {overallStatus}
        </span>
      </div>

      <div className="space-y-4 p-4">
        <div className="grid grid-cols-2 gap-2">
          <MetricCard
            label="CPU"
            value={normalizeMetric(metrics.cpu)}
            icon={Cpu}
            color="text-cyan-300"
          />

          <MetricCard
            label="Memory"
            value={normalizeMetric(metrics.memory)}
            icon={MemoryStick}
            color="text-purple-300"
          />

          <MetricCard
            label="Disk"
            value={normalizeMetric(metrics.disk)}
            icon={HardDrive}
            color="text-green-300"
          />

          <MetricCard
            label="Network"
            value={normalizeMetric(metrics.network)}
            icon={Network}
            color="text-orange-300"
          />
        </div>

        <div className="rounded-lg border border-cyan-950 bg-[#041326] p-3">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">
              Service Status
            </p>

            <p className="text-[10px] text-slate-500">
              {operationalCount}/{serviceCount} operational
            </p>
          </div>

          <div className="space-y-2">
            {services.map((service, index) => {
              const name =
                service?.name || `Service ${index + 1}`;
              const status =
                service?.status || "Unknown";

              return (
                <div
                  key={`${name}-${index}`}
                  className="flex items-center justify-between gap-2 border-b border-cyan-950 pb-2 last:border-0 last:pb-0"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    {name.toLowerCase().includes("database") ? (
                      <Database
                        size={13}
                        className="shrink-0 text-slate-400"
                      />
                    ) : name.toLowerCase().includes("firewall") ? (
                      <ShieldCheck
                        size={13}
                        className="shrink-0 text-slate-400"
                      />
                    ) : name.toLowerCase().includes("websocket") ? (
                      <Radio
                        size={13}
                        className="shrink-0 text-slate-400"
                      />
                    ) : (
                      <Server
                        size={13}
                        className="shrink-0 text-slate-400"
                      />
                    )}

                    <span className="truncate text-xs text-slate-300">
                      {name}
                    </span>
                  </div>

                  <span
                    className={`flex shrink-0 items-center gap-1 text-[10px] ${getStatusClass(
                      status
                    )}`}
                  >
                    {getStatusIcon(status)}
                    {status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-500">
          <div>
            <p>API</p>
            <p
              className={
                apiHealthy
                  ? "mt-1 text-green-300"
                  : "mt-1 text-red-300"
              }
            >
              {apiHealthy ? "Online" : "Offline"}
            </p>
          </div>

          <div>
            <p>Realtime</p>
            <p
              className={
                wsConnected
                  ? "mt-1 text-cyan-300"
                  : "mt-1 text-yellow-300"
              }
            >
              {wsConnected ? "WebSocket" : "Polling"}
            </p>
          </div>

          <div>
            <p>Events</p>
            <p className="mt-1 text-slate-300">
              {attacks.length.toLocaleString()}
            </p>
          </div>

          <div>
            <p>Updated</p>
            <p className="mt-1 truncate text-slate-300">
              {updatedAt}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}