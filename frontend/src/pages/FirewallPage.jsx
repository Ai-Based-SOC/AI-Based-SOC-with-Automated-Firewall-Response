import { useEffect, useMemo, useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Line,
} from "react-simple-maps";

import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import {
  blockIpApi,
  unblockIpApi,
  getAttacksApi,
  checkThreatIntelApi,
  getGeoIntelApi,
} from "../services/api";

const geoUrl =
  "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/world/world.json";

const CENTER_COORDINATES = [78.9629, 20.5937];

function normalizeAttacks(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (response && Array.isArray(response.data)) {
    return response.data;
  }

  if (response && Array.isArray(response.attacks)) {
    return response.attacks;
  }

  if (response && Array.isArray(response.items)) {
    return response.items;
  }

  if (response && Array.isArray(response.results)) {
    return response.results;
  }

  return [];
}

function getIp(attack) {
  return (
    attack?.attacker_ip ||
    attack?.source_ip ||
    attack?.src_ip ||
    attack?.ip_address ||
    attack?.ip ||
    ""
  );
}

function getSeverity(attack) {
  const value = String(
    attack?.severity ||
      attack?.risk_level ||
      attack?.threat_level ||
      "low"
  ).toLowerCase();

  if (value === "critical") return "Critical";
  if (value === "high") return "High";
  if (value === "medium") return "Medium";
  if (value === "low") return "Low";

  return "Other";
}

function getAttackType(attack) {
  const value = String(
    attack?.attack_type ||
      attack?.attackType ||
      attack?.type ||
      "Unknown"
  );

  if (/ddos|dos/i.test(value)) {
    return "DoS";
  }

  if (/brute|force/i.test(value)) {
    return "Brute Force";
  }

  if (/scan/i.test(value)) {
    return "Port Scan";
  }

  if (/web/i.test(value)) {
    return "Web Attack";
  }

  if (/malware/i.test(value)) {
    return "Malware";
  }

  return value;
}

function normalizeCoordinates(value) {
  if (!value) {
    return null;
  }

  if (Array.isArray(value) && value.length >= 2) {
    const longitude = Number(value[0]);
    const latitude = Number(value[1]);

    if (
      Number.isFinite(longitude) &&
      Number.isFinite(latitude) &&
      longitude >= -180 &&
      longitude <= 180 &&
      latitude >= -90 &&
      latitude <= 90
    ) {
      return [longitude, latitude];
    }
  }

  const latitude = Number(
    value.latitude ??
      value.lat ??
      value.location?.latitude ??
      value.location?.lat
  );

  const longitude = Number(
    value.longitude ??
      value.lon ??
      value.lng ??
      value.location?.longitude ??
      value.location?.lon ??
      value.location?.lng
  );

  if (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    longitude >= -180 &&
    longitude <= 180 &&
    latitude >= -90 &&
    latitude <= 90
  ) {
    return [longitude, latitude];
  }

  return null;
}

function getGeoCoordinates(response) {
  if (!response) {
    return null;
  }

  const candidates = [
    response,
    response.data,
    response.location,
    response.geo,
    response.geolocation,
    response.result,
  ];

  for (const candidate of candidates) {
    const coordinates = normalizeCoordinates(candidate);

    if (coordinates) {
      return coordinates;
    }
  }

  return null;
}

function getLocationName(response) {
  if (!response) {
    return "Location unavailable";
  }

  const candidates = [
    response,
    response.data,
    response.location,
    response.geo,
    response.geolocation,
    response.result,
  ];

  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== "object") {
      continue;
    }

    const value =
      candidate.city ||
      candidate.country ||
      candidate.country_name ||
      candidate.region ||
      candidate.location_name ||
      candidate.display_name;

    if (value) {
      return String(value);
    }
  }

  return "Location unavailable";
}

function severityClasses(severity) {
  switch (severity) {
    case "Critical":
      return "bg-red-500/20 text-red-400 border-red-500/30";

    case "High":
      return "bg-orange-500/20 text-orange-400 border-orange-500/30";

    case "Medium":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";

    case "Low":
      return "bg-green-500/20 text-green-400 border-green-500/30";

    default:
      return "bg-slate-500/20 text-slate-400 border-slate-500/30";
  }
}

export default function FirewallPage({ profile, onLogout }) {
  const [attacks, setAttacks] = useState([]);
  const [selectedIp, setSelectedIp] = useState("");
  const [blockedIps, setBlockedIps] = useState([]);
  const [threatIntel, setThreatIntel] = useState(null);

  const [geoLocations, setGeoLocations] = useState({});
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState("");

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [activeTab, setActiveTab] = useState("overview");

  /* ---------------------------------------------------------------------- */
  /* LOAD ATTACKS                                                           */
  /* ---------------------------------------------------------------------- */

  useEffect(() => {
    let mounted = true;

    async function loadAttacks() {
      try {
        setLoading(true);

        const response = await getAttacksApi(300);

        if (!mounted) {
          return;
        }

        setAttacks(normalizeAttacks(response));
        setError("");
      } catch (err) {
        console.error("Firewall attack loading error:", err);

        if (mounted) {
          setError("Unable to load attack data.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadAttacks();

    const interval = setInterval(loadAttacks, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  /* ---------------------------------------------------------------------- */
  /* UNIQUE ATTACKER IPS                                                    */
  /* ---------------------------------------------------------------------- */

  const attackerIps = useMemo(() => {
    const set = new Set();

    attacks.forEach((attack) => {
      const ip = getIp(attack);

      if (ip) {
        set.add(ip);
      }
    });

    return Array.from(set);
  }, [attacks]);

  /* ---------------------------------------------------------------------- */
  /* GEOLOCATION                                                            */
  /* ---------------------------------------------------------------------- */

  useEffect(() => {
    let mounted = true;

    async function loadGeoLocations() {
      if (attackerIps.length === 0) {
        return;
      }

      setGeoLoading(true);
      setGeoError("");

      const nextLocations = {};

      for (const ip of attackerIps.slice(0, 25)) {
        try {
          const response = await getGeoIntelApi(ip);

          if (!mounted) {
            return;
          }

          const coordinates = getGeoCoordinates(response);

          if (coordinates) {
            nextLocations[ip] = {
              coordinates,
              name: getLocationName(response),
            };
          }
        } catch (err) {
          console.warn(
            `Unable to retrieve geolocation for ${ip}:`,
            err
          );
        }
      }

      if (!mounted) {
        return;
      }

      setGeoLocations(nextLocations);
      setGeoLoading(false);

      if (
        Object.keys(nextLocations).length === 0 &&
        attackerIps.length > 0
      ) {
        setGeoError("No geolocation data available for the detected IPs.");
      }
    }

    loadGeoLocations();

    return () => {
      mounted = false;
    };
  }, [attackerIps]);

  /* ---------------------------------------------------------------------- */
  /* SELECT IP                                                               */
  /* ---------------------------------------------------------------------- */

  async function handleSelectIp(ip) {
    setSelectedIp(ip);
    setMessage("");
    setError("");
    setThreatIntel(null);

    if (!ip) {
      return;
    }

    try {
      const response = await checkThreatIntelApi(ip);

      setThreatIntel(response);
    } catch (err) {
      console.warn("Threat intelligence lookup failed:", err);
    }
  }

  /* ---------------------------------------------------------------------- */
  /* BLOCK IP                                                                */
  /* ---------------------------------------------------------------------- */

  async function handleBlockIp() {
    if (!selectedIp) {
      setError("Select an attacker IP first.");
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setMessage("");

      await blockIpApi(selectedIp);

      setBlockedIps((previous) => {
        if (previous.includes(selectedIp)) {
          return previous;
        }

        return [...previous, selectedIp];
      });

      setMessage(`${selectedIp} has been submitted for firewall blocking.`);
    } catch (err) {
      console.error("Block IP error:", err);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to block the selected IP."
      );
    } finally {
      setActionLoading(false);
    }
  }

  /* ---------------------------------------------------------------------- */
  /* UNBLOCK IP                                                              */
  /* ---------------------------------------------------------------------- */

  async function handleUnblockIp() {
    if (!selectedIp) {
      setError("Select an attacker IP first.");
      return;
    }

    try {
      setActionLoading(true);
      setError("");
      setMessage("");

      await unblockIpApi(selectedIp);

      setBlockedIps((previous) =>
        previous.filter((ip) => ip !== selectedIp)
      );

      setMessage(`${selectedIp} has been submitted for firewall unblocking.`);
    } catch (err) {
      console.error("Unblock IP error:", err);

      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Unable to unblock the selected IP."
      );
    } finally {
      setActionLoading(false);
    }
  }

  /* ---------------------------------------------------------------------- */
  /* ATTACK SUMMARY                                                          */
  /* ---------------------------------------------------------------------- */

  const criticalCount = attacks.filter(
    (attack) => getSeverity(attack) === "Critical"
  ).length;

  const highCount = attacks.filter(
    (attack) => getSeverity(attack) === "High"
  ).length;

  const blockedCount = blockedIps.length;

  const geoCount = Object.keys(geoLocations).length;

  /* ---------------------------------------------------------------------- */
  /* MAP MARKERS                                                             */
  /* ---------------------------------------------------------------------- */

  const geoMarkers = Object.entries(geoLocations);

  return (
    <PageShell profile={profile} onLogout={onLogout}>
      <div className="min-h-screen bg-[#020b1c] p-4 text-white md:p-6">

        {/* HEADER */}
        <div className="mb-6">

          <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">

            <div>
              <h1 className="text-2xl font-bold">
                Firewall Operations
              </h1>

              <p className="mt-1 text-sm text-slate-400">
                Windows firewall monitoring, threat intelligence and IP response
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-2 text-sm text-green-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
              Firewall Monitoring Active
            </div>

          </div>
        </div>

        {/* MESSAGES */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {message && (
          <div className="mb-4 rounded-lg border border-green-500/30 bg-green-500/10 p-4 text-sm text-green-300">
            {message}
          </div>
        )}

        {/* KPI */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <div className="rounded-xl border border-slate-800 bg-[#071426] p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Security Events
            </p>

            <p className="mt-2 text-3xl font-bold text-cyan-400">
              {attacks.length.toLocaleString()}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#071426] p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Critical Threats
            </p>

            <p className="mt-2 text-3xl font-bold text-red-400">
              {criticalCount.toLocaleString()}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#071426] p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              High Threats
            </p>

            <p className="mt-2 text-3xl font-bold text-orange-400">
              {highCount.toLocaleString()}
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#071426] p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Blocked IPs
            </p>

            <p className="mt-2 text-3xl font-bold text-green-400">
              {blockedCount.toLocaleString()}
            </p>
          </div>

        </div>

        {/* TABS */}
        <div className="mb-6 flex flex-wrap gap-2">

          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              activeTab === "overview"
                ? "bg-cyan-500 text-slate-950"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            Overview
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("events")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              activeTab === "events"
                ? "bg-cyan-500 text-slate-950"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            Attack Events
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("blocked")}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              activeTab === "blocked"
                ? "bg-cyan-500 text-slate-950"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            Blocked IPs
          </button>

        </div>

        {/* OVERVIEW */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">

            {/* MAP */}
            <Panel title="Attacker Geolocation">

              <div className="relative h-[450px] overflow-hidden rounded-lg bg-[#030914]">

                {geoLoading && (
                  <div className="absolute left-4 top-4 z-10 rounded-lg border border-cyan-500/20 bg-slate-950/90 px-3 py-2 text-xs text-cyan-400">
                    Loading geolocation...
                  </div>
                )}

                {geoError && !geoLoading && (
                  <div className="absolute left-4 top-4 z-10 rounded-lg border border-yellow-500/20 bg-slate-950/90 px-3 py-2 text-xs text-yellow-400">
                    {geoError}
                  </div>
                )}

                <ComposableMap
                  projection="geoMercator"
                  projectionConfig={{
                    scale: 115,
                    center: CENTER_COORDINATES,
                  }}
                  width={800}
                  height={450}
                  style={{
                    width: "100%",
                    height: "100%",
                  }}
                >

                  <Geographies geography={geoUrl}>
                    {({ geographies }) =>
                      geographies.map((geo) => (
                        <Geography
                          key={geo.rsmKey}
                          geography={geo}
                          fill="#0f1b2d"
                          stroke="#26364f"
                          strokeWidth={0.5}
                          style={{
                            default: {
                              outline: "none",
                            },
                            hover: {
                              fill: "#16263d",
                              outline: "none",
                            },
                            pressed: {
                              outline: "none",
                            },
                          }}
                        />
                      ))
                    }
                  </Geographies>

                  {/* USER / SOC LOCATION */}
                  <Marker coordinates={CENTER_COORDINATES}>
                    <circle
                      r={4}
                      fill="#22d3ee"
                      stroke="#ffffff"
                      strokeWidth={1}
                    />

                    <text
                      textAnchor="middle"
                      y={-10}
                      style={{
                        fill: "#67e8f9",
                        fontSize: "10px",
                        fontWeight: 600,
                      }}
                    >
                      SOC
                    </text>
                  </Marker>

                  {/* REAL GEOLOCATION MARKERS */}
                  {geoMarkers.map(([ip, location]) => {

                    const coordinates = location?.coordinates;

                    if (
                      !Array.isArray(coordinates) ||
                      coordinates.length < 2
                    ) {
                      return null;
                    }

                    return (
                      <g key={ip}>

                        <Line
                          from={coordinates}
                          to={CENTER_COORDINATES}
                          stroke="#ef4444"
                          strokeWidth={1.2}
                          strokeLinecap="round"
                        />

                        <Marker coordinates={coordinates}>

                          <circle
                            r={5}
                            fill="#ef4444"
                            stroke="#ffffff"
                            strokeWidth={1}
                          />

                          <text
                            textAnchor="middle"
                            y={-9}
                            style={{
                              fill: "#fca5a5",
                              fontSize: "9px",
                              fontWeight: 600,
                            }}
                          >
                            {ip}
                          </text>

                        </Marker>

                      </g>
                    );
                  })}

                </ComposableMap>

                {geoMarkers.length === 0 && !geoLoading && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="rounded-lg border border-slate-700 bg-slate-950/80 px-4 py-3 text-center">
                      <p className="text-sm text-slate-300">
                        No attacker locations available
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        The backend did not return usable coordinates.
                      </p>
                    </div>
                  </div>
                )}

              </div>

              <div className="mt-4 flex justify-between text-xs text-slate-500">
                <span>
                  Geolocated attackers: {geoCount}
                </span>

                <span>
                  Location source: SOC backend
                </span>
              </div>

            </Panel>

            {/* RESPONSE PANEL */}
            <Panel title="Firewall Response">

              <div className="space-y-5">

                <div>
                  <label className="mb-2 block text-sm text-slate-400">
                    Attacker IP
                  </label>

                  <select
                    value={selectedIp}
                    onChange={(event) =>
                      handleSelectIp(event.target.value)
                    }
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500"
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
                </div>

                {selectedIp && (
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">

                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Selected IP
                    </p>

                    <p className="mt-1 font-mono text-lg text-cyan-400">
                      {selectedIp}
                    </p>

                    {geoLocations[selectedIp] && (
                      <p className="mt-2 text-sm text-slate-400">
                        Location:{" "}
                        {geoLocations[selectedIp].name}
                      </p>
                    )}

                  </div>
                )}

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">

                  <button
                    type="button"
                    disabled={!selectedIp || actionLoading}
                    onClick={handleBlockIp}
                    className="rounded-lg bg-red-600 px-4 py-3 text-sm font-semibold text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Block IP"}
                  </button>

                  <button
                    type="button"
                    disabled={!selectedIp || actionLoading}
                    onClick={handleUnblockIp}
                    className="rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {actionLoading
                      ? "Processing..."
                      : "Unblock IP"}
                  </button>

                </div>

                {threatIntel && (
                  <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-4">

                    <h3 className="text-sm font-semibold text-purple-300">
                      Threat Intelligence
                    </h3>

                    <pre className="mt-3 max-h-60 overflow-auto whitespace-pre-wrap break-words text-xs text-slate-400">
                      {JSON.stringify(
                        threatIntel,
                        null,
                        2
                      )}
                    </pre>

                  </div>
                )}

                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">

                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    Firewall Provider
                  </p>

                  <p className="mt-2 text-sm font-medium text-slate-200">
                    Windows Defender Firewall
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Firewall actions are executed through the SOC backend.
                  </p>

                </div>

              </div>

            </Panel>

          </div>
        )}

        {/* ATTACK EVENTS */}
        {activeTab === "events" && (
          <Panel title="Attack Events">

            <div className="overflow-x-auto">

              <table className="w-full min-w-[900px] text-left">

                <thead>
                  <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">

                    <th className="px-4 py-3">
                      IP Address
                    </th>

                    <th className="px-4 py-3">
                      Attack Type
                    </th>

                    <th className="px-4 py-3">
                      Severity
                    </th>

                    <th className="px-4 py-3">
                      Location
                    </th>

                    <th className="px-4 py-3">
                      Action
                    </th>

                  </tr>
                </thead>

                <tbody>

                  {loading ? (
                    <tr>
                      <td
                        colSpan="5"
                        className="px-4 py-10 text-center text-sm text-slate-500"
                      >
                        Loading attack events...
                      </td>
                    </tr>
                  ) : attacks.length === 0 ? (
                    <tr>
                      <td
                        colSpan="5"
                        className="px-4 py-10 text-center text-sm text-slate-500"
                      >
                        No attack events available.
                      </td>
                    </tr>
                  ) : (
                    attacks.slice(0, 100).map((attack, index) => {

                      const ip = getIp(attack);
                      const severity = getSeverity(attack);

                      return (
                        <tr
                          key={
                            attack?.id ||
                            attack?._id ||
                            attack?.event_id ||
                            `${ip}-${index}`
                          }
                          className="border-b border-slate-900 hover:bg-slate-900/40"
                        >

                          <td className="px-4 py-4 font-mono text-sm text-cyan-400">
                            {ip || "Unknown"}
                          </td>

                          <td className="px-4 py-4 text-sm text-slate-200">
                            {getAttackType(attack)}
                          </td>

                          <td className="px-4 py-4">

                            <span
                              className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${severityClasses(
                                severity
                              )}`}
                            >
                              {severity}
                            </span>

                          </td>

                          <td className="px-4 py-4 text-sm text-slate-400">
                            {geoLocations[ip]?.name ||
                              "Location unavailable"}
                          </td>

                          <td className="px-4 py-4 text-sm text-slate-300">
                            {String(
                              attack?.action_taken ||
                                attack?.action ||
                                "Detected"
                            )}
                          </td>

                        </tr>
                      );
                    })
                  )}

                </tbody>

              </table>

            </div>

          </Panel>
        )}

        {/* BLOCKED IPS */}
        {activeTab === "blocked" && (
          <Panel title="Blocked IP Addresses">

            {blockedIps.length === 0 ? (
              <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-10 text-center">
                <p className="text-sm text-slate-400">
                  No IP addresses have been blocked during this session.
                </p>
              </div>
            ) : (
              <div className="space-y-3">

                {blockedIps.map((ip) => (
                  <div
                    key={ip}
                    className="flex flex-col justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/40 p-4 sm:flex-row sm:items-center"
                  >

                    <div>
                      <p className="font-mono text-sm text-cyan-400">
                        {ip}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Windows Defender Firewall
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setSelectedIp(ip);
                        handleUnblockIp();
                      }}
                      disabled={actionLoading}
                      className="rounded-lg bg-green-600 px-4 py-2 text-xs font-semibold text-white hover:bg-green-500 disabled:opacity-40"
                    >
                      Unblock
                    </button>

                  </div>
                ))}

              </div>
            )}

          </Panel>
        )}

        {/* FOOTER */}
        <div className="mt-5 flex flex-col justify-between gap-2 text-xs text-slate-600 sm:flex-row">

          <span>
            {attacks.length.toLocaleString()} security events loaded
          </span>

          <span>
            Geolocation data: backend supplied only
          </span>

        </div>

      </div>
    </PageShell>
  );
}