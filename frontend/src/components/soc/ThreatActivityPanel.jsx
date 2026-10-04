import { BarChart, Bar, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import Panel from "../Panel";

export default function ThreatActivityPanel({ data, total }) {
  return (
    <Panel title="Threat Activity" className="bg-[#071a2f] border-cyan-900/60">
      <div className="mb-2 flex items-end justify-between">
        <p className="text-2xl font-semibold text-cyan-300">{total}</p>
        <p className="text-xs text-slate-400">total monitored events</p>
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip cursor={{ fill: "rgba(34,211,238,0.08)" }} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((item) => (
                <Cell key={item.name} fill={item.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}
