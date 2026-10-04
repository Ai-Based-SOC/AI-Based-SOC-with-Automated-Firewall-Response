import React from "react";
import {
  DonutChart,
  Donut,
  Cell,
  ResponsiveContainer,
  Label,
  Tooltip
} from "recharts";

const threatCategories = [
  { name: "Critical", id: "critical", color: "#EF4444" },
  { name: "High", id: "high", color: "#F59E0B" },
  { name: "Medium", id: "medium", color: "#EAB308" },
  { name: "Low", id: "low", color: "#38BDF8" },
  { name: "Other", id: "other", color: "#A78BFA" }
];

export function ThreatDistribution({ distributionData }) {
  const defaultData = [
    { name: "Critical", value: 12 },
    { name: "High", value: 34 },
    { name: "Medium", value: 56 },
    { name: "Low", value: 89 },
    { name: "Other", value: 23 }
  ];

  const data = distributionData || defaultData;

  return (
    <div>
      <h3 className="soc-heading mb-3">Threat Distribution</h3>
      <DonutChart width="100%" height="300">
        <Donut
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={70}
          outerRadius={110}
          fill={({ dataItem }) => {
            const category = threatCategories.find(
              (c) => c.name === dataItem.name
            );
            return category ? category.color : "#A78BFA";
          }}
        >
          {data.map((item, index) => (
            <Cell key={item.name} />
          ))}
          <Label
            type="value"
            position="inside"
            value={({ payload }) => payload.value}
            fontSize={12}
            fill="#888"
          />
          <Tooltip />
        </Donut>
      </DonutChart>
    </div>
  );
}