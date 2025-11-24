import { Card } from "@/components/ui/card";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { ShareOfVoice } from "@shared/schema";

interface ShareOfVoiceChartProps {
  shareOfVoice: ShareOfVoice[];
}

const COLORS = [
  "hsl(217, 91%, 60%)",  
  "hsl(351, 83%, 58%)",  
  "hsl(43, 96%, 56%)",    
  "hsl(271, 81%, 56%)",  
  "hsl(173, 58%, 47%)",   
  "hsl(168, 76%, 42%)",   
];

export function ShareOfVoiceChart({ shareOfVoice }: ShareOfVoiceChartProps) {
  // ✅ FIXED: Ensure we have data and use correct field names
  const chartData = (shareOfVoice || [])
    .filter((item) => item && typeof item === "object")
    .map((item) => ({
      name: item.brand || "Unknown",
      value: Number(item.percentage) || 0,
    }))
    .filter((item) => item.value > 0);

  // If no data with positive values, show message
  if (!chartData || chartData.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Share of Voice</h3>
        <div className="text-muted-foreground text-center py-8">
          No share of voice data available yet
        </div>
      </Card>
    );
  }

  // Custom label renderer to avoid overlap
  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    payload,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = outerRadius + 35;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="hsl(var(--foreground))"
        textAnchor={x > cx ? "start" : "end"}
        dominantBaseline="central"
        style={{ fontSize: "13px", fontWeight: "500" }}
      >
        {`${payload.value.toFixed(1)}%`}
      </text>
    );
  };


  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Share of Voice</h3>
      {/* ✅ FIXED: Optimized layout for better text visibility */}
      <ResponsiveContainer width="100%" height={500}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="42%"
            labelLine={{
              stroke: "hsl(var(--muted-foreground))",
              strokeWidth: 1,
              length: 20,
            }}
            label={renderCustomLabel}
            outerRadius={120}
            innerRadius={0}
            fill="hsl(var(--primary))"
            dataKey="value"
            paddingAngle={2}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                stroke="hsl(var(--background))"
                strokeWidth={2}
              />
            ))}
          </Pie>
          {/* ✅ FIXED: Better legend with proper text wrapping */}
          <Legend
            verticalAlign="bottom"
            align="center"
            layout="horizontal"
            wrapperStyle={{
              paddingTop: "35px",
              fontSize: "13px",
              lineHeight: "22px",
              maxWidth: "100%",
            }}
            iconType="circle"
            iconSize={8}
            formatter={(value: string, entry: any) => {
              const percentage = entry.payload.value.toFixed(1);
              // Format: "Brand Name (XX.X%)"
              const displayName =
                value.length > 30 ? `${value.substring(0, 27)}...` : value;
              return `${displayName} (${percentage}%)`;
            }}
          />
          {/* ✅ Enhanced tooltip */}
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value.toFixed(1)}%`,
              name,
            ]}
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              padding: "10px 14px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            }}
            itemStyle={{
              color: "hsl(var(--foreground))",
              fontSize: "14px",
              padding: "2px 0",
            }}
            labelStyle={{
              color: "hsl(var(--foreground))",
              fontWeight: "600",
              marginBottom: "6px",
              fontSize: "14px",
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
}
