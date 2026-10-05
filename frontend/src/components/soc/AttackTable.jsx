import { Link } from "react-router-dom";

function severityClass(value) {
  const severity = String(value || "low").toLowerCase();

  if (severity === "critical") {
    return "bg-red-500/20 text-red-300";
  }

  if (severity === "high") {
    return "bg-orange-500/20 text-orange-300";
  }

  if (severity === "medium") {
    return "bg-yellow-500/20 text-yellow-300";
  }

  return "bg-green-500/20 text-green-300";
}

function timestampOf(row) {
  return (
    row?.timestamp ||
    row?.created_at ||
    row?.detected_at ||
    row?.event_time
  );
}

export default function AttackTable({ attacks = [] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-cyan-900/70">
      <table className="min-w-[900px] w-full text-left text-xs">
        <thead className="bg-[#041326] text-slate-500">
          <tr>
            <th className="px-3 py-3">Time</th>
            <th className="px-3 py-3">IP Address</th>
            <th className="px-3 py-3">Attack Type</th>
            <th className="px-3 py-3">Severity</th>
            <th className="px-3 py-3">Location</th>
            <th className="px-3 py-3">Status</th>
            <th className="px-3 py-3">Action</th>
          </tr>
        </thead>

        <tbody>
          {attacks.map((attack, index) => (
            <tr
              key={
                attack?.id ||
                `${attack?.source_ip}-${timestampOf(attack)}-${index}`
              }
              className="border-t border-cyan-950 hover:bg-cyan-950/40"
            >
              <td className="whitespace-nowrap px-3 py-3 text-slate-500">
                {timestampOf(attack)
                  ? new Date(timestampOf(attack)).toLocaleString()
                  : "--"}
              </td>

              <td className="px-3 py-3 font-mono text-cyan-300">
                {attack?.source_ip || attack?.attacker_ip || "--"}
              </td>

              <td className="px-3 py-3 text-slate-200">
                {attack?.attack_type || attack?.type || "--"}
              </td>

              <td className="px-3 py-3">
                <span
                  className={`rounded-full px-2 py-1 text-[10px] font-semibold capitalize ${severityClass(
                    attack?.severity
                  )}`}
                >
                  {attack?.severity || "low"}
                </span>
              </td>

              <td className="px-3 py-3 text-slate-400">
                {attack?.country ||
                  attack?.location ||
                  attack?.source_country ||
                  "Unknown"}
              </td>

              <td className="px-3 py-3 text-slate-400">
                {attack?.status || attack?.action_taken || "Detected"}
              </td>

              <td className="px-3 py-3">
                {attack?.id ? (
                  <Link
                    to={`/attacks/${attack.id}`}
                    className="text-cyan-300 hover:text-cyan-100"
                  >
                    View
                  </Link>
                ) : (
                  "--"
                )}
              </td>
            </tr>
          ))}

          {attacks.length === 0 && (
            <tr>
              <td
                colSpan={7}
                className="px-3 py-10 text-center text-slate-500"
              >
                No attack data available.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}