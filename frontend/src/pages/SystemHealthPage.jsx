import { useCallback, useEffect, useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

import Panel from "../components/Panel";
import { getAttacksApi } from "../services/api";

const HEALTH_API =
  "http://127.0.0.1:8001/api/v1/system-health";

const REFRESH_INTERVAL = 30000;

export default function SystemHealthPage({ profile }) {
  const [health, setHealth] = useState({
    status: "Operational",
    uptimePercent: 99.9,
    cpu: 0,
    ram: 0,
    disk: 0,

    alerts: {
      total: 0,
      blocked: 0,
    },

    connections: {
      ssh: 0,
      http: 0,
      https: 0,
      dns: 0,
    },
  });

  const [attacks, setAttacks] = useState([]);

  const [loading, setLoading] = useState(true);
  const [attackLoading, setAttackLoading] = useState(false);
  const [error, setError] = useState("");

  /*
   * Safely convert a value into a number.
   */
  const toNumber = (value, fallback = 0) => {
    const number = Number(value);

    return Number.isFinite(number) ? number : fallback;
  };

  /*
   * Keep percentage values between 0 and 100.
   */
  const clampPercent = (value) => {
    return Math.min(Math.max(toNumber(value), 0), 100);
  };

  /*
   * Fetch live Windows/SOC system health from backend.
   */
  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(HEALTH_API, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(
          `System health API returned HTTP ${response.status}`
        );
      }

      const data = await response.json();

      /*
       * Backend compatibility:
       *
       * CPU:
       * data.cpu
       * data.cpu_usage
       * data.metrics.cpu
       *
       * RAM:
       * data.ram
       * data.memory_usage
       * data.memory
       * data.metrics.ram
       *
       * Disk:
       * data.disk
       * data.disk_usage
       * data.metrics.disk
       */

      const cpu = clampPercent(
        data.cpu ??
          data.cpu_usage ??
          data.metrics?.cpu ??
          data.metrics?.cpu_usage ??
          0
      );

      const ram = clampPercent(
        data.ram ??
          data.memory_usage ??
          data.memory ??
          data.ram_usage ??
          data.metrics?.ram ??
          data.metrics?.memory ??
          data.metrics?.memory_usage ??
          0
      );

      const disk = clampPercent(
        data.disk ??
          data.disk_usage ??
          data.storage_usage ??
          data.metrics?.disk ??
          data.metrics?.disk_usage ??
          0
      );

      const uptimePercent = clampPercent(
        data.uptime_percent ??
          data.uptimePercent ??
          data.uptime ??
          99.9
      );

      const totalAlerts = toNumber(
        data.alerts?.total ??
          data.status_counts?.total ??
          data.total_alerts ??
          data.alert_count ??
          0
      );

      const blockedAlerts = toNumber(
        data.alerts?.blocked ??
          data.status_counts?.blocked ??
          data.blocked ??
          data.blocked_count ??
          0
      );

      const connections = data.connections ?? {};

      setHealth({
        status:
          data.status ??
          data.health_status ??
          "Operational",

        uptimePercent,

        cpu,
        ram,
        disk,

        alerts: {
          total: totalAlerts,
          blocked: blockedAlerts,
        },

        connections: {
          ssh: toNumber(
            connections.ssh ??
              connections.SSH ??
              data.ssh_connections ??
              0
          ),

          http: toNumber(
            connections.http ??
              connections.HTTP ??
              data.http_connections ??
              0
          ),

          https: toNumber(
            connections.https ??
              connections.HTTPS ??
              data.https_connections ??
              0
          ),

          dns: toNumber(
            connections.dns ??
              connections.DNS ??
              data.dns_connections ??
              0
          ),
        },
      });
    } catch (err) {
      console.error(
        "Failed to fetch system health:",
        err
      );

      setError(
        err?.message ||
          "Unable to connect to the system health backend."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  /*
   * Fetch real attack data.
   *
   * The risk distribution chart is calculated from
   * the actual attacks returned by the SOC backend.
   */
  const fetchAttacks = useCallback(async () => {
    setAttackLoading(true);

    try {
      const result = await getAttacksApi(500);

      /*
       * Support different API response formats:
       *
       * [
       *   {...}
       * ]
       *
       * {
       *   attacks: [...]
       * }
       *
       * {
       *   data: [...]
       * }
       */
      let attackList = [];

      if (Array.isArray(result)) {
        attackList = result;
      } else if (Array.isArray(result?.attacks)) {
        attackList = result.attacks;
      } else if (Array.isArray(result?.data)) {
        attackList = result.data;
      } else if (Array.isArray(result?.items)) {
        attackList = result.items;
      }

      setAttacks(attackList);
    } catch (err) {
      console.error(
        "Failed to fetch attack data:",
        err
      );

      /*
       * Don't destroy the system-health page if
       * attack API is temporarily unavailable.
       */
      setAttacks([]);
    } finally {
      setAttackLoading(false);
    }
  }, []);

  /*
   * Initial load + automatic refresh.
   */
  useEffect(() => {
    fetchHealth();
    fetchAttacks();

    const healthInterval = setInterval(
      fetchHealth,
      REFRESH_INTERVAL
    );

    const attackInterval = setInterval(
      fetchAttacks,
      REFRESH_INTERVAL
    );

    return () => {
      clearInterval(healthInterval);
      clearInterval(attackInterval);
    };
  }, [fetchHealth, fetchAttacks]);

  /*
   * Calculate real risk/severity distribution
   * from attack records.
   */
  const riskDistribution = useMemo(() => {
    const distribution = {
      Critical: 0,
      High: 0,
      Medium: 0,
      Low: 0,
    };

    attacks.forEach((attack) => {
      const severity = String(
        attack?.severity ??
          attack?.risk_level ??
          attack?.risk ??
          "low"
      ).toLowerCase();

      if (severity === "critical") {
        distribution.Critical += 1;
      } else if (severity === "high") {
        distribution.High += 1;
      } else if (severity === "medium") {
        distribution.Medium += 1;
      } else {
        distribution.Low += 1;
      }
    });

    return [
      {
        name: "Critical",
        value: distribution.Critical,
      },
      {
        name: "High",
        value: distribution.High,
      },
      {
        name: "Medium",
        value: distribution.Medium,
      },
      {
        name: "Low",
        value: distribution.Low,
      },
    ];
  }, [attacks]);

  /*
   * Total attacks.
   */
  const totalAttacks = useMemo(() => {
    return attacks.length;
  }, [attacks]);

  /*
   * Critical attacks.
   */
  const criticalAttacks = useMemo(() => {
    return attacks.filter((attack) => {
      const severity = String(
        attack?.severity ??
          attack?.risk_level ??
          attack?.risk ??
          ""
      ).toLowerCase();

      return severity === "critical";
    }).length;
  }, [attacks]);

  /*
   * High-risk attacks.
   */
  const highAttacks = useMemo(() => {
    return attacks.filter((attack) => {
      const severity = String(
        attack?.severity ??
          attack?.risk_level ??
          attack?.risk ??
          ""
      ).toLowerCase();

      return severity === "high";
    }).length;
  }, [attacks]);

  /*
   * Use backend alert count if available.
   * Otherwise use the actual attack count.
   */
  const totalAlerts =
    health.alerts.total > 0
      ? health.alerts.total
      : totalAttacks;

  /*
   * Use backend blocked count if available.
   * Otherwise calculate blocked attacks from attack data.
   */
  const calculatedBlocked = useMemo(() => {
    return attacks.filter((attack) => {
      const action = String(
        attack?.action_taken ??
          attack?.action ??
          attack?.response ??
          ""
      ).toLowerCase();

      return (
        action.includes("block") ||
        action.includes("blocked") ||
        action.includes("deny") ||
        action.includes("denied")
      );
    }).length;
  }, [attacks]);

  const blockedAlerts =
    health.alerts.blocked > 0
      ? health.alerts.blocked
      : calculatedBlocked;

  /*
   * Determine overall SOC health.
   */
  const systemStatus = useMemo(() => {
    const backendStatus = String(
      health.status || "Operational"
    ).toLowerCase();

    if (
      backendStatus.includes("offline") ||
      backendStatus.includes("down")
    ) {
      return "Offline";
    }

    if (
      backendStatus.includes("degraded") ||
      backendStatus.includes("warning")
    ) {
      return "Degraded";
    }

    if (
      health.cpu >= 95 ||
      health.ram >= 95 ||
      health.disk >= 95
    ) {
      return "Critical";
    }

    if (
      health.cpu >= 85 ||
      health.ram >= 85 ||
      health.disk >= 90
    ) {
      return "Warning";
    }

    return "Operational";
  }, [
    health.status,
    health.cpu,
    health.ram,
    health.disk,
  ]);

  /*
   * Status styling.
   */
  const getStatusStyle = () => {
    switch (systemStatus) {
      case "Critical":
      case "Offline":
        return {
          text: "text-red-400",
          dot: "bg-red-400",
          border: "border-red-500/30",
          background: "bg-red-500/10",
        };

      case "Warning":
      case "Degraded":
        return {
          text: "text-yellow-400",
          dot: "bg-yellow-400",
          border: "border-yellow-500/30",
          background: "bg-yellow-500/10",
        };

      default:
        return {
          text: "text-green-400",
          dot: "bg-green-400",
          border: "border-green-500/30",
          background: "bg-green-500/10",
        };
    }
  };

  const statusStyle = getStatusStyle();

  /*
   * Resource progress bar styling.
   */
  const getUsageClass = (value) => {
    if (value >= 90) {
      return "bg-red-500";
    }

    if (value >= 75) {
      return "bg-yellow-500";
    }

    return "bg-cyan-500";
  };

  /*
   * Risk chart colors.
   */
  const riskColors = {
    Critical: "#ef4444",
    High: "#f97316",
    Medium: "#eab308",
    Low: "#22c55e",
  };

  /*
   * Active connection information.
   */
  const connectionData = [
    {
      protocol: "SSH",
      hosts: health.connections.ssh,
    },
    {
      protocol: "HTTP",
      hosts: health.connections.http,
    },
    {
      protocol: "HTTPS",
      hosts: health.connections.https,
    },
    {
      protocol: "DNS",
      hosts: health.connections.dns,
    },
  ];

  /*
   * Format current time for UI.
   */
  const currentTime = new Date().toLocaleTimeString(
    "en-IN",
    {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }
  );

  /*
   * Manual refresh for both APIs.
   */
  const handleRefresh = async () => {
    await Promise.all([
      fetchHealth(),
      fetchAttacks(),
    ]);
  };

  return (
    <div className="min-h-screen bg-[#020b1c] text-white p-6">
      {/* ========================================================= */}
      {/* HEADER */}
      {/* ========================================================= */}

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="soc-heading">
              System Health
            </h1>

            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${statusStyle.text} ${statusStyle.border} ${statusStyle.background}`}
            >
              <span
                className={`h-2 w-2 rounded-full ${statusStyle.dot} ${
                  systemStatus === "Operational"
                    ? "animate-pulse"
                    : ""
                }`}
              />

              {systemStatus}
            </span>
          </div>

          <p className="text-sm text-slate-400 mt-1">
            Real-time Windows infrastructure and SOC
            health monitoring
          </p>

          <p className="text-xs text-slate-500 mt-1">
            Last checked: {currentTime}
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading || attackLoading}
          className="soc-btn disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading || attackLoading
            ? "Refreshing..."
            : "Refresh Metrics"}
        </button>
      </div>

      {/* ========================================================= */}
      {/* ERROR MESSAGE */}
      {/* ========================================================= */}

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
          <div className="text-sm font-medium text-red-400">
            System Health API Error
          </div>

          <div className="text-xs text-red-300/80 mt-1">
            {error}
          </div>

          <div className="text-xs text-slate-500 mt-2">
            Backend endpoint:
            {" "}
            {HEALTH_API}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SYSTEM STATUS + UPTIME */}
      {/* ========================================================= */}

      <Panel title="System Metrics">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Status */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-sm text-slate-400">
              System Status
            </div>

            <div
              className={`flex items-center gap-2 text-xl font-semibold mt-2 ${statusStyle.text}`}
            >
              <span
                className={`h-3 w-3 rounded-full ${statusStyle.dot}`}
              />

              {systemStatus}
            </div>

            <div className="text-xs text-slate-500 mt-2">
              Backend: {health.status}
            </div>
          </div>

          {/* Uptime */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-sm text-slate-400">
              System Uptime
            </div>

            <div className="text-2xl font-semibold text-cyan-400 mt-2">
              {health.uptimePercent.toFixed(2)}%
            </div>

            <div className="h-2 bg-slate-800 rounded-full mt-3 overflow-hidden">
              <div
                className="h-2 bg-cyan-500 rounded-full transition-all duration-700"
                style={{
                  width: `${Math.min(
                    Math.max(
                      health.uptimePercent,
                      0
                    ),
                    100
                  )}%`,
                }}
              />
            </div>
          </div>
        </div>

        {/* ======================================================= */}
        {/* CPU / RAM / DISK */}
        {/* ======================================================= */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* CPU */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm text-slate-400">
                  CPU Usage
                </div>

                <div className="text-xs text-slate-500 mt-1">
                  Windows processor
                </div>
              </div>

              <div className="text-xl font-semibold text-cyan-400">
                {health.cpu.toFixed(1)}%
              </div>
            </div>

            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-700 ${getUsageClass(
                  health.cpu
                )}`}
                style={{
                  width: `${health.cpu}%`,
                }}
              />
            </div>
          </div>

          {/* RAM */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm text-slate-400">
                  Memory Usage
                </div>

                <div className="text-xs text-slate-500 mt-1">
                  Windows RAM utilization
                </div>
              </div>

              <div className="text-xl font-semibold text-cyan-400">
                {health.ram.toFixed(1)}%
              </div>
            </div>

            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-700 ${getUsageClass(
                  health.ram
                )}`}
                style={{
                  width: `${health.ram}%`,
                }}
              />
            </div>
          </div>

          {/* DISK */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-sm text-slate-400">
                  Disk Usage
                </div>

                <div className="text-xs text-slate-500 mt-1">
                  Windows storage utilization
                </div>
              </div>

              <div className="text-xl font-semibold text-cyan-400">
                {health.disk.toFixed(1)}%
              </div>
            </div>

            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-700 ${getUsageClass(
                  health.disk
                )}`}
                style={{
                  width: `${health.disk}%`,
                }}
              />
            </div>
          </div>
        </div>
      </Panel>

      {/* ========================================================= */}
      {/* SOC ALERT SUMMARY */}
      {/* ========================================================= */}

      <Panel title="SOC Alert Summary">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total */}
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-sm text-slate-400">
              Total Alerts
            </div>

            <div className="text-2xl font-semibold text-cyan-400 mt-2">
              {totalAlerts}
            </div>

            <div className="text-xs text-slate-500 mt-1">
              Current attack records
            </div>
          </div>

          {/* Critical */}
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">
            <div className="text-sm text-slate-400">
              Critical
            </div>

            <div className="text-2xl font-semibold text-red-400 mt-2">
              {criticalAttacks}
            </div>

            <div className="text-xs text-slate-500 mt-1">
              Critical severity attacks
            </div>
          </div>

          {/* High */}
          <div className="rounded-lg border border-orange-500/20 bg-orange-500/5 p-4">
            <div className="text-sm text-slate-400">
              High Risk
            </div>

            <div className="text-2xl font-semibold text-orange-400 mt-2">
              {highAttacks}
            </div>

            <div className="text-xs text-slate-500 mt-1">
              High severity attacks
            </div>
          </div>

          {/* Blocked */}
          <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4">
            <div className="text-sm text-slate-400">
              Blocked
            </div>

            <div className="text-2xl font-semibold text-green-400 mt-2">
              {blockedAlerts}
            </div>

            <div className="text-xs text-slate-500 mt-1">
              Automated/manual responses
            </div>
          </div>
        </div>
      </Panel>

      {/* ========================================================= */}
      {/* RISK DISTRIBUTION */}
      {/* ========================================================= */}

      <Panel title="Risk Distribution">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Chart */}
          <div className="h-80">
            {totalAttacks > 0 ? (
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={75}
                    outerRadius={115}
                    paddingAngle={3}
                    stroke="none"
                  >
                    {riskDistribution.map(
                      (entry) => (
                        <Cell
                          key={entry.name}
                          fill={
                            riskColors[
                              entry.name
                            ]
                          }
                        />
                      )
                    )}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      backgroundColor:
                        "#0f172a",
                      border:
                        "1px solid #334155",
                      borderRadius:
                        "8px",
                      color: "#fff",
                    }}
                    itemStyle={{
                      color: "#fff",
                    }}
                  />

                  <Legend
                    verticalAlign="bottom"
                    height={36}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center rounded-lg border border-slate-700/50 bg-slate-900/40">
                <div className="text-center">
                  <div className="text-slate-400 text-sm">
                    No attack data available
                  </div>

                  <div className="text-slate-600 text-xs mt-1">
                    The chart will populate when
                    attacks are returned by the SOC API.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Risk details */}
          <div className="flex flex-col justify-center space-y-3">
            {riskDistribution.map(
              (risk) => (
                <div
                  key={risk.name}
                  className="flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-900/40 p-4"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{
                        backgroundColor:
                          riskColors[
                            risk.name
                          ],
                      }}
                    />

                    <span className="text-sm text-slate-300">
                      {risk.name}
                    </span>
                  </div>

                  <span className="font-mono text-sm text-white">
                    {risk.value}
                  </span>
                </div>
              )
            )}

            <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-4 mt-2">
              <div className="text-xs text-slate-400">
                Total analyzed attacks
              </div>

              <div className="text-2xl font-semibold text-cyan-400 mt-1">
                {totalAttacks}
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* ========================================================= */}
      {/* ACTIVE CONNECTIONS */}
      {/* ========================================================= */}

      <Panel title="Active Connections">
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Header */}
            <div className="grid grid-cols-3 gap-4 border-b border-slate-700/50 pb-3">
              <div className="text-xs uppercase tracking-wider text-slate-500">
                Protocol
              </div>

              <div className="text-xs uppercase tracking-wider text-slate-500">
                Connections
              </div>

              <div className="text-xs uppercase tracking-wider text-slate-500">
                Status
              </div>
            </div>

            {/* Rows */}
            <div>
              {connectionData.map(
                (connection) => {
                  const healthy =
                    connection.hosts >= 0;

                  return (
                    <div
                      key={
                        connection.protocol
                      }
                      className="grid grid-cols-3 gap-4 items-center border-b border-slate-700/30 py-4"
                    >
                      <span className="font-mono text-sm text-cyan-400">
                        {connection.protocol}
                      </span>

                      <span className="text-sm text-slate-300">
                        {connection.hosts}{" "}
                        {connection.hosts === 1
                          ? "connection"
                          : "connections"}
                      </span>

                      <div>
                        <span
                          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
                            healthy
                              ? "border-green-500/30 bg-green-500/10 text-green-400"
                              : "border-yellow-500/30 bg-yellow-500/10 text-yellow-400"
                          }`}
                        >
                          <span
                            className={`h-2 w-2 rounded-full ${
                              healthy
                                ? "bg-green-400"
                                : "bg-yellow-400"
                            }`}
                          />

                          Healthy
                        </span>
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          </div>
        </div>
      </Panel>

      {/* ========================================================= */}
      {/* SYSTEM INFORMATION */}
      {/* ========================================================= */}

      <Panel title="Monitoring Information">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-xs text-slate-500">
              Monitoring Mode
            </div>

            <div className="text-sm text-cyan-400 mt-1">
              Live
            </div>
          </div>

          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-xs text-slate-500">
              Refresh Interval
            </div>

            <div className="text-sm text-cyan-400 mt-1">
              30 seconds
            </div>
          </div>

          <div className="rounded-lg border border-slate-700/50 bg-slate-900/40 p-4">
            <div className="text-xs text-slate-500">
              Platform
            </div>

            <div className="text-sm text-cyan-400 mt-1">
              Windows
            </div>
          </div>
        </div>
      </Panel>

      {/* ========================================================= */}
      {/* ACTIONS */}
      {/* ========================================================= */}

      <div className="mt-8 pt-8 border-t border-slate-700/40">
        <h2 className="soc-heading mb-4">
          Actions
        </h2>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading || attackLoading}
            className="soc-btn disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading || attackLoading
              ? "Refreshing..."
              : "Refresh Metrics"}
          </button>

          <button
            type="button"
            className="soc-btn soc-btn-secondary"
            onClick={() => {
              window.print();
            }}
          >
            Export Health Report
          </button>
        </div>
      </div>
    </div>
  );
}