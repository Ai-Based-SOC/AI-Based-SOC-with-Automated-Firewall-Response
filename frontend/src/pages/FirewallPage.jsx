import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Activity,
  Ban,
  CheckCircle,
  MapPin,
  Shield,
  Unlock,
} from "lucide-react";

import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import {
  blockIpApi,
  checkThreatIntelApi,
  getAttacksApi,
  getGeoIntelApi,
  unblockIpApi,
} from "../services/api";
import { connectAttackSocket } from "../services/socket";

function normalizeAttacks(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.attacks)) return payload.attacks;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;

  return [];
}

function attackKey(attack) {
  return (
    attack?.id ||
    attack?._id ||
    [
      attack?.source_ip || "",
      attack?.timestamp ||
        attack?.created_at ||
        "",
      attack?.attack_type || "",
    ].join("|")
  );
}

function mergeAttacks(incoming, current) {
  const seen = new Set();

  return [...incoming, ...current]
    .filter((attack) => {
      const key = attackKey(attack);

      if (seen.has(key)) {
        return false;
      }

      seen.add(key);
      return true;
    })
    .slice(0, 1000);
}

function getIp(attack) {
  return (
    attack?.source_ip ||
    attack?.attacker_ip ||
    attack?.src_ip ||
    attack?.ip_address ||
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

function getAttackType(attack) {
  return (
    attack?.attack_type ||
    attack?.attackType ||
    attack?.type ||
    "Unknown"
  );
}

function getAction(attack) {
  return String(
    attack?.action_taken ||
      attack?.action ||
      attack?.recommended_action ||
      "Detected"
  );
}

function severityClass(value) {
  if (value === "critical") {
    return "bg-red-500/20 text-red-300 border-red-500/30";
  }

  if (value === "high") {
    return "bg-orange-500/20 text-orange-300 border-orange-500/30";
  }

  if (value === "medium") {
    return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30";
  }

  return "bg-green-500/20 text-green-300 border-green-500/30";
}

function getCoordinates(response) {
  const candidate =
    response?.data ||
    response?.location ||
    response?.geo ||
    response?.geolocation ||
    response;

  if (!candidate || typeof candidate !== "object") {
    return null;
  }

  const latitude = Number(
    candidate.latitude ??
      candidate.lat ??
      candidate.location?.latitude ??
      candidate.location?.lat
  );

  const longitude = Number(
    candidate.longitude ??
      candidate.lon ??
      candidate.lng ??
      candidate.location?.longitude ??
      candidate.location?.lon ??
      candidate.location?.lng
  );

  if (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  ) {
    return {
      latitude,
      longitude,
      label:
        candidate.city ||
        candidate.country ||
        candidate.country_name ||
        "Unknown",
    };
  }

  return null;
}

export default function FirewallPage({
  profile,
  onLogout,
}) {
  const [attacks, setAttacks] = useState([]);
  const [blockedIps, setBlockedIps] = useState([]);
  const [selectedIp, setSelectedIp] = useState("");
  const [selectedIntel, setSelectedIntel] = useState(null);
  const [locations, setLocations] = useState({});
  const [firewallEvents, setFirewallEvents] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadAttacks = useCallback(async () => {
    try {
      const response = await getAttacksApi(500);
      const rows = normalizeAttacks(response?.data ?? response);

      setAttacks((current) => mergeAttacks(rows, current));

      const blockedFromEvents = rows
        .filter((attack) => {
          const action = getAction(attack).toLowerCase();
          const status = String(
            attack?.status || ""
          ).toLowerCase();

          return (
            action.includes("block") ||
            status.includes("block")
          );
        })
        .map(getIp)
        .filter((ip) => ip !== "Unknown");

      setBlockedIps((current) => [
        ...new Set([
          ...current,
          ...blockedFromEvents,
        ]),
      ]);
    } catch (requestError) {
      console.error("Firewall loading error:", requestError);
      setError("Unable to load firewall events.");
    } finally {
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
      onMessage: (event) => {
        if (event?.event === "new_attack") {
          const attack =
            event.data ||
            event.attack ||
            event.item;

          if (attack) {
            setAttacks((current) =>
              mergeAttacks([attack], current)
            );
          }

          return;
        }

        if (event?.event === "firewall_action") {
          const action =
            event.data ||
            event.payload;

          if (!action?.ip_address) {
            return;
          }

          setFirewallEvents((current) => [
            {
              ...action,
              received_at: new Date().toISOString(),
            },
            ...current,
          ].slice(0, 50));

          if (action.action === "block") {
            setBlockedIps((current) => [
              ...new Set([
                action.ip_address,
                ...current,
              ]),
            ]);

            setMessage(
              `Firewall update: ${action.ip_address} blocked.`
            );
          }

          if (action.action === "unblock") {
            setBlockedIps((current) =>
              current.filter(
                (ip) => ip !== action.ip_address
              )
            );

            setMessage(
              `Firewall update: ${action.ip_address} unblocked.`
            );
          }
        }
      },
    });

    return () => {
      window.clearInterval(timer);
      disconnect?.();
    };
  }, [loadAttacks]);

  const attackerIps = useMemo(() => {
    return [
      ...new Set(
        attacks
          .map(getIp)
          .filter((ip) => ip !== "Unknown")
      ),
    ];
  }, [attacks]);

  useEffect(() => {
    let active = true;

    async function loadLocations() {
      const values = await Promise.all(
        attackerIps.slice(0, 20).map(async (ip) => {
          try {
            const response = await getGeoIntelApi(ip);
            const location = getCoordinates(response);

            return location ? [ip, location] : null;
          } catch {
            return null;
          }
        })
      );

      if (active) {
        setLocations(
          Object.fromEntries(values.filter(Boolean))
        );
      }
    }

    if (attackerIps.length) {
      loadLocations();
    }

    return () => {
      active = false;
    };
  }, [attackerIps]);

  const criticalCount = attacks.filter(
    (attack) => getSeverity(attack) === "critical"
  ).length;

  const highCount = attacks.filter(
    (attack) => getSeverity(attack) === "high"
  ).length;

  async function selectIp(ip) {
    setSelectedIp(ip);
    setSelectedIntel(null);
    setMessage("");
    setError("");

    if (!ip) return;

    try {
      const response = await checkThreatIntelApi(ip);
      setSelectedIntel(response?.data ?? response);
    } catch {
      setError("Threat intelligence lookup failed.");
    }
  }

  async function blockSelectedIp() {
    if (!selectedIp) {
      setError("Select an attacker IP first.");
      return;
    }

    try {
      setActionLoading(true);
      setMessage("");
      setError("");

      await blockIpApi(selectedIp);

      setBlockedIps((current) => [
        ...new Set([
          selectedIp,
          ...current,
        ]),
      ]);

      setMessage(
        `${selectedIp} was submitted for blocking.`
      );
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          "Unable to block the selected IP."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function unblockSelectedIp(ip = selectedIp) {
    if (!ip) {
      setError("Select an IP address first.");
      return;
    }

    try {
      setActionLoading(true);
      setMessage("");
      setError("");

      await unblockIpApi(ip);

      setBlockedIps((current) =>
        current.filter((value) => value !== ip)
      );

      setMessage(
        `${ip} was submitted for unblocking.`
      );
    } catch (requestError) {
      setError(
        requestError?.response?.data?.detail ||
          "Unable to unblock the selected IP."
      );
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <PageShell
      title="Firewall"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto max-w-[1600px] space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">
              Firewall Operations
            </h2>

            <p className="text-sm text-slate-400">
              Windows firewall monitoring, threat intelligence and IP response
            </p>
          </div>

          <span
            className={`rounded-lg border px-3 py-2 text-xs ${
              wsConnected
                ? "border-green-500/30 bg-green-500/10 text-green-300"
                : "border-yellow-500/30 bg-yellow-500/10 text-yellow-300"
            }`}
          >
            ● {wsConnected ? "Live monitoring" : "Polling monitoring"}
          </span>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {message && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-300">
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              Security Events
            </p>
            <p className="mt-2 text-3xl font-bold text-cyan-300">
              {attacks.length}
            </p>
          </div>

          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              Critical Threats
            </p>
            <p className="mt-2 text-3xl font-bold text-red-300">
              {criticalCount}
            </p>
          </div>

          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              High Threats
            </p>
            <p className="mt-2 text-3xl font-bold text-orange-300">
              {highCount}
            </p>
          </div>

          <div className="rounded-xl border border-cyan-900/70 bg-[#071426] p-4">
            <p className="text-xs uppercase text-slate-500">
              Blocked IPs
            </p>
            <p className="mt-2 text-3xl font-bold text-green-300">
              {blockedIps.length}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            ["overview", "Overview"],
            ["events", "Attack Events"],
            ["blocked", "Blocked IPs"],
          ].map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                activeTab === key
                  ? "bg-cyan-500 text-slate-950"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === "overview" && (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Panel
              title="Attacker Geolocation"
              icon={<MapPin size={16} />}
            >
              <div className="relative min-h-[420px] overflow-hidden rounded-lg border border-cyan-900 bg-[#031326]">
                <div className="absolute inset-0 bg-[linear-gradient(rgba(34,211,238,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(34,211,238,0.08)_1px,transparent_1px)] bg-[size:32px_32px]" />

                <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center">
                  <div className="h-4 w-4 animate-pulse rounded-full bg-cyan-300 shadow-[0_0_20px_#22d3ee]" />
                  <span className="mt-1 text-[10px] text-cyan-300">
                    SOC
                  </span>
                </div>

                {Object.entries(locations).map(([ip, location]) => (
                  <div
                    key={ip}
                    className="absolute"
                    style={{
                      left: `${((location.longitude + 180) / 360) * 100}%`,
                      top: `${((90 - location.latitude) / 180) * 100}%`,
                    }}
                  >
                    <div className="h-3 w-3 animate-pulse rounded-full bg-red-400 shadow-[0_0_16px_#ef4444]" />

                    <span className="absolute left-4 top-0 whitespace-nowrap rounded bg-black/70 px-1 text-[9px] text-red-200">
                      {ip}
                    </span>
                  </div>
                ))}

                {!Object.keys(locations).length && (
                  <div className="absolute inset-0 grid place-items-center">
                    <div className="rounded-lg border border-slate-700 bg-[#020b1c]/90 p-4 text-center">
                      <p className="text-sm text-slate-300">
                        {loading
                          ? "Loading attacker locations..."
                          : "No geolocation data available"}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-3 flex justify-between text-xs text-slate-500">
                <span>
                  Geolocated attackers:{" "}
                  {Object.keys(locations).length}
                </span>

                <span>Backend location service</span>
              </div>
            </Panel>

            <Panel
              title="Firewall Response"
              icon={<Shield size={16} />}
            >
              <div className="space-y-4">
                <label className="block text-sm text-slate-400">
                  Attacker IP

                  <select
                    value={selectedIp}
                    onChange={(event) =>
                      selectIp(event.target.value)
                    }
                    className="mt-1 w-full rounded-lg border border-cyan-900 bg-[#041326] px-3 py-3 text-sm"
                  >
                    <option value="">
                      Select attacker IP
                    </option>

                    {attackerIps.map((ip) => (
                      <option key={ip} value={ip}>
                        {ip}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={blockSelectedIp}
                    disabled={!selectedIp || actionLoading}
                    className="flex items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-3 text-sm font-semibold hover:bg-red-500 disabled:opacity-40"
                  >
                    <Ban size={16} />
                    {actionLoading ? "Processing..." : "Block IP"}
                  </button>

                  <button
                    type="button"
                    onClick={() => unblockSelectedIp()}
                    disabled={!selectedIp || actionLoading}
                    className="flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold hover:bg-green-500 disabled:opacity-40"
                  >
                    <Unlock size={16} />
                    {actionLoading ? "Processing..." : "Unblock IP"}
                  </button>
                </div>

                {selectedIntel && (
                  <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-4">
                    <p className="text-sm font-semibold text-purple-300">
                      Threat Intelligence
                    </p>

                    <div className="mt-3 space-y-2 text-sm">
                      <p>
                        Reputation:{" "}
                        <span className="text-orange-300">
                          {selectedIntel.reputation_score ?? "--"}
                        </span>
                      </p>

                      <p>
                        Country:{" "}
                        <span className="text-cyan-300">
                          {selectedIntel.country || "Unknown"}
                        </span>
                      </p>

                      <p>
                        Malicious:{" "}
                        <span
                          className={
                            selectedIntel.malicious
                              ? "text-red-300"
                              : "text-green-300"
                          }
                        >
                          {selectedIntel.malicious
                            ? "Yes"
                            : "No"}
                        </span>
                      </p>
                    </div>
                  </div>
                )}

                <div className="rounded-lg border border-cyan-900 bg-[#041326] p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle
                      size={17}
                      className="text-green-300"
                    />

                    <span className="text-sm font-semibold">
                      Windows Defender Firewall
                    </span>
                  </div>

                  <p className="mt-2 text-xs text-slate-500">
                    Firewall actions are executed through the authenticated SOC
                    backend.
                  </p>
                </div>
              </div>
            </Panel>
          </div>
        )}

        {activeTab === "events" && (
          <Panel
            title="Attack Events"
            icon={<Activity size={16} />}
          >
            <div className="overflow-x-auto">
              <table className="min-w-[900px] w-full text-left text-xs">
                <thead className="border-b border-cyan-900/70 text-slate-500">
                  <tr>
                    <th className="px-3 py-3">IP Address</th>
                    <th className="px-3 py-3">Attack Type</th>
                    <th className="px-3 py-3">Severity</th>
                    <th className="px-3 py-3">Action</th>
                    <th className="px-3 py-3">Status</th>
                  </tr>
                </thead>

                <tbody>
                  {attacks.map((attack, index) => {
                    const severity = getSeverity(attack);

                    return (
                      <tr
                        key={`${attackKey(attack)}-${index}`}
                        className="border-b border-cyan-950 hover:bg-cyan-950/40"
                      >
                        <td className="px-3 py-3 font-mono text-cyan-300">
                          {getIp(attack)}
                        </td>

                        <td className="px-3 py-3 text-slate-200">
                          {getAttackType(attack)}
                        </td>

                        <td className="px-3 py-3">
                          <span
                            className={`rounded-full border px-2 py-1 text-[10px] capitalize ${severityClass(
                              severity
                            )}`}
                          >
                            {severity}
                          </span>
                        </td>

                        <td className="px-3 py-3 text-slate-300">
                          {getAction(attack)}
                        </td>

                        <td className="px-3 py-3 text-slate-400">
                          {attack?.status || "Detected"}
                        </td>
                      </tr>
                    );
                  })}

                  {!attacks.length && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-3 py-10 text-center text-slate-500"
                      >
                        No attack events available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Panel>
        )}

        {activeTab === "blocked" && (
          <Panel title="Blocked IP Addresses">
            {!blockedIps.length ? (
              <div className="rounded-lg border border-cyan-900 bg-[#041326] p-10 text-center text-sm text-slate-500">
                No blocked IP addresses are currently recorded.
              </div>
            ) : (
              <div className="space-y-3">
                {blockedIps.map((ip) => (
                  <div
                    key={ip}
                    className="flex flex-col justify-between gap-3 rounded-lg border border-cyan-900 bg-[#041326] p-4 sm:flex-row sm:items-center"
                  >
                    <div>
                      <p className="font-mono text-cyan-300">
                        {ip}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Windows Defender Firewall
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => unblockSelectedIp(ip)}
                      disabled={actionLoading}
                      className="rounded-lg bg-green-600 px-4 py-2 text-xs font-semibold hover:bg-green-500 disabled:opacity-50"
                    >
                      Unblock
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        )}

        <Panel title="Live Firewall Actions">
          {firewallEvents.length === 0 ? (
            <p className="text-sm text-slate-500">
              Waiting for firewall actions...
            </p>
          ) : (
            <div className="space-y-2">
              {firewallEvents.map((event, index) => (
                <div
                  key={`${event.ip_address}-${event.received_at}-${index}`}
                  className="flex items-center justify-between gap-3 rounded-lg border border-cyan-900 bg-[#041326] p-3"
                >
                  <div>
                    <p className="font-mono text-sm text-cyan-300">
                      {event.ip_address}
                    </p>

                    <p className="text-xs text-slate-500">
                      {event.reason || "SOC analyst action"}
                    </p>
                  </div>

                  <span
                    className={
                      event.action === "block"
                        ? "text-xs text-red-300"
                        : "text-xs text-green-300"
                    }
                  >
                    {event.action}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </PageShell>
  );
}