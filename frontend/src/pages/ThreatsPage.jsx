import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import { Search, ShieldAlert } from "lucide-react";

import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import { getAttacksApi } from "../services/api";
import { connectAttackSocket } from "../services/socket";

const COLORS = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#06b6d4",
  "#8b5cf6",
];

function normalizeAttacks(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.attacks)) return payload.attacks;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;

  return [];
}

function getAttackKey(attack) {
  return (
    attack?.id ||
    attack?._id ||
    [
      attack?.source_ip || attack?.attacker_ip || "",
      attack?.destination_ip || "",
      attack?.attack_type || "",
      attack?.timestamp || attack?.created_at || "",
    ].join("|")
  );
}

function mergeAttacks(incoming, current) {
  const seen = new Set();

  return [...incoming, ...current]
    .filter((attack) => {
      const key = getAttackKey(attack);

      if (seen.has(key)) {
        return false;
      }

      seen.add(key);
      return true;
    })
    .slice(0, 1000);
}

function getTimestamp(attack) {
  return (
    attack?.timestamp ||
    attack?.created_at ||
    attack?.detected_at ||
    attack?.event_time ||
    null
  );
}

function getSourceIp(attack) {
  return (
    attack?.source_ip ||
    attack?.attacker_ip ||
    attack?.src_ip ||
    "Unknown"
  );
}

function getAttackType(attack) {
  return (
    attack?.attack_type ||
    attack?.attackType ||
    attack?.type ||
    "Unknown"
  );
}

function getSeverity(attack) {
  return String(
    attack?.severity ||
      attack?.risk_level ||
      attack?.threat_level ||
      "low"
  ).toLowerCase();
}

function severityClass(severity) {
  if (severity === "critical") {
    return "bg-red-500/20 text-red-300 border-red-500/30";
  }

  if (severity === "high") {
    return "bg-orange-500/20 text-orange-300 border-orange-500/30";
  }

  if (severity === "medium") {
    return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30";
  }

  return "bg-green-500/20 text-green-300 border-green-500/30";
}

export default function ThreatsPage({ profile, onLogout }) {
  const [attacks, setAttacks] = useState([]);
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const requestInFlightRef = useRef(false);

  const loadAttacks = useCallback(async () => {
    if (requestInFlightRef.current) return;

    requestInFlightRef.current = true;

    try {
      const response = await getAttacksApi(500);
      const rows = normalizeAttacks(response?.data ?? response);

      setAttacks((current) => mergeAttacks(rows, current));
    } catch (error) {
      console.error("Threat loading error:", error);
    } finally {
      requestInFlightRef.current = false;
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAttacks();

    const timer = window.setInterval(loadAttacks, 5000);

    const disconnect = connectAttackSocket({
      onOpen: () => setWsConnected(true),
      onClose: () => setWsConnected(false),
      onError: () => setWsConnected(false),
      onMessage: (message) => {
        const item =
          message?.data ||
          message?.attack ||
          message?.item;

        if (item) {
          setAttacks((current) => mergeAttacks([item], current));
        }
      },
    });

    return () => {
      window.clearInterval(timer);
      disconnect?.();
    };
  }, [loadAttacks]);

  const attackTypes = useMemo(() => {
    return [
      ...new Set(attacks.map(getAttackType)),
    ];
  }, [attacks]);

  const filteredAttacks = useMemo(() => {
    const query = search.trim().toLowerCase();

    return attacks.filter((attack) => {
      const matchesSearch =
        !query ||
        JSON.stringify(attack).toLowerCase().includes(query);

      const matchesSeverity =
        severityFilter === "all" ||
        getSeverity(attack) === severityFilter;

      const matchesType =
        typeFilter === "all" ||
        getAttackType(attack) === typeFilter;

      return matchesSearch && matchesSeverity && matchesType;
    });
  }, [attacks, search, severityFilter, typeFilter]);

  const pieData = useMemo(() => {
    const counts = new Map();

    attacks.forEach((attack) => {
      const type = getAttackType(attack);
      counts.set(type, (counts.get(type) || 0) + 1);
    });

    const rows = [...counts.entries()].map(([name, value]) => ({
      name,
      value,
    }));

    return rows.length
      ? rows
      : [{ name: "No Data", value: 1 }];
  }, [attacks]);

  const normalRisk = useMemo(() => {
    return attacks
      .filter((attack) => Number(attack?.risk_score || 0) < 70)
      .map((attack, index) => ({
        x: index + 1,
        y: Number(attack?.risk_score || 0),
      }));
  }, [attacks]);

  const highRisk = useMemo(() => {
    return attacks
      .filter((attack) => Number(attack?.risk_score || 0) >= 70)
      .map((attack, index) => ({
        x: index + 1,
        y: Number(attack?.risk_score || 0),
      }));
  }, [attacks]);

  const criticalCount = attacks.filter(
    (attack) => getSeverity(attack) === "critical"
  ).length;

  const highCount = attacks.filter(
    (attack) => getSeverity(attack) === "high"
  ).length;

  const mediumCount = attacks.filter(
    (attack) => getSeverity(attack) === "medium"
  ).length;

  const lowCount = attacks.filter(
    (attack) => getSeverity(attack) === "low"
  ).length;

  return (
    <PageShell
      title="Threats"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1600px] space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">Threat Analysis</h2>
            <p className="text-sm text-slate-400">
              View and manage all detected threats
            </p>
          </div>

          <span
            className={`rounded-lg border px-3 py-2 text-xs ${
              wsConnected
                ? "border-green-500/30 bg-green-500/10 text-green-300"
                : "border-yellow-500/30 bg-yellow-500/10 text-yellow-300"
            }`}
          >
            ● {wsConnected ? "Live stream connected" : "Polling mode"}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            ["Critical", criticalCount, "text-red-300"],
            ["High", highCount, "text-orange-300"],
            ["Medium", mediumCount, "text-yellow-300"],
            ["Low", lowCount, "text-green-300"],
          ].map(([label, value, color]) => (
            <div
              key={label}
              className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4"
            >
              <p className="text-xs uppercase text-slate-500">{label}</p>
              <p className={`mt-2 text-2xl font-bold ${color}`}>
                {value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>

        <Panel>
          <div className="flex flex-col gap-3 lg:flex-row">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              />

              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search IP, attack type, location..."
                className="w-full rounded-lg border border-cyan-900 bg-[#041326] py-2 pl-9 pr-3 text-sm outline-none focus:border-cyan-400"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(event) =>
                setSeverityFilter(event.target.value)
              }
              className="rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
              className="rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm"
            >
              <option value="all">All Attack Types</option>
              {attackTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </Panel>

        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <Panel
            title="Attack Classification"
            icon={<ShieldAlert size={16} />}
          >
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={85}
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#071426",
                      border: "1px solid #164e63",
                    }}
                  />

                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel
            title="Risk Analysis"
            className="xl:col-span-2"
          >
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <XAxis dataKey="x" name="Event" />
                  <YAxis dataKey="y" name="Risk" domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Scatter
                    name="Normal"
                    data={normalRisk}
                    fill="#22c55e"
                  />
                  <Scatter
                    name="High Risk"
                    data={highRisk}
                    fill="#ef4444"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </div>

        <Panel title="Live Threats">
          <div className="overflow-x-auto">
            <table className="min-w-[1050px] w-full text-left text-xs">
              <thead className="border-b border-cyan-900/70 text-slate-500">
                <tr>
                  <th className="px-3 py-3">Time</th>
                  <th className="px-3 py-3">IP Address</th>
                  <th className="px-3 py-3">Attack Type</th>
                  <th className="px-3 py-3">Severity</th>
                  <th className="px-3 py-3">Risk</th>
                  <th className="px-3 py-3">Location</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3">Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredAttacks.map((attack, index) => {
                  const severity = getSeverity(attack);
                  const timestamp = getTimestamp(attack);

                  return (
                    <tr
                      key={`${getAttackKey(attack)}-${index}`}
                      className="border-b border-cyan-950 hover:bg-cyan-950/40"
                    >
                      <td className="whitespace-nowrap px-3 py-3 text-slate-500">
                        {timestamp
                          ? new Date(timestamp).toLocaleString()
                          : "--"}
                      </td>

                      <td className="px-3 py-3 font-mono text-cyan-300">
                        {getSourceIp(attack)}
                      </td>

                      <td className="px-3 py-3 text-slate-200">
                        {getAttackType(attack)}
                      </td>

                      <td className="px-3 py-3">
                        <span
                          className={`rounded-full border px-2 py-1 text-[10px] font-semibold capitalize ${severityClass(
                            severity
                          )}`}
                        >
                          {severity}
                        </span>
                      </td>

                      <td className="px-3 py-3 text-slate-300">
                        {attack?.risk_score ?? "--"}
                      </td>

                      <td className="px-3 py-3 text-slate-400">
                        {attack?.country ||
                          attack?.location ||
                          attack?.source_country ||
                          "Unknown"}
                      </td>

                      <td className="px-3 py-3 text-slate-400">
                        {attack?.status ||
                          attack?.action_taken ||
                          "Detected"}
                      </td>

                      <td className="px-3 py-3">
                        {attack?.id ? (
                          <Link
                            to={`/attacks/${attack.id}`}
                            className="text-cyan-300 hover:text-white"
                          >
                            View
                          </Link>
                        ) : (
                          "--"
                        )}
                      </td>
                    </tr>
                  );
                })}

                {!filteredAttacks.length && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-3 py-12 text-center text-slate-500"
                    >
                      {loading
                        ? "Loading threats..."
                        : "No threats match the selected filters."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </PageShell>
  );
}