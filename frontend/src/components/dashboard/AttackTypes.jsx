import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

const attackTypeCategories = [
  { name: "DoS", id: "dos", color: "#EF4444" },
  { name: "Brute Force", id: "brute", color: "#F59E0B" },
  { name: "Port Scan", id: "port", color: "#38BDF8" },
  { name: "Web Attack", id: "web", color: "#A78BFA" },
  { name: "Malware", id: "malware", color: "#22C55E" },
  { name: "Other", id: "other", color: "#F472B6" }
];

export function AttackTypes({ attackTypesData }) {
  const defaultData = [
    { name: "DoS", count: 45, risk: 87 },
    { name: "Brute Force", count: 32, risk: 72 },
    { name: "Port Scan", count: 67, risk: 45 },
    { name: "Web Attack", count: 28, risk: 91 },
    { name: "Malware", count: 15, risk: 63 },
    { name: "Other", count: 12, risk: 38 }
  ];

  const data = attackTypesData || defaultData;

  return (
    <div>
      <h3 className="soc-heading mb-3">Attack Types</h3>
      <ResponsiveContainer width="100%" height="300">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: "#888" }}
            domain={["0", "100"]}
          />
          <YAxis tick={{ fontSize: 10, fill: "#888" }} />
          <Tooltip />
          <Legend verticalAlign="top" height={36} />
          {data.map((item, index) => (
            <Bar
              key={item.name}
              dataKey="count"
              fill={({ dataItem }) =>
                attackTypeCategories.find((c) => c.name === dataItem.name)?.color ||
                "#A78BFA"
              }
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}