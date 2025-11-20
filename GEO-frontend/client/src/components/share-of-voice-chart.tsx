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
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export function ShareOfVoiceChart({ shareOfVoice }: ShareOfVoiceChartProps) {
  // ✅ FIXED: Ensure we have data and use correct field names
  const chartData = (shareOfVoice || [])
    .filter(item => item && typeof item === 'object')
    .map((item) => ({
      name: item.brand || "Unknown",
      value: Number(item.percentage) || 0,
    }))
    .filter(item => item.value > 0);

  // If no data with positive values, show message
  if (!chartData || chartData.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="font-semibold text-lg mb-4">Share of Voice</h3>
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          No share of voice data available yet
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="font-semibold text-lg mb-4">Share of Voice</h3>
      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name}: ${(entry.value).toFixed(1)}%`}
              outerRadius={80}
              fill="hsl(var(--primary))"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number) => `${value.toFixed(1)}%`}
              contentStyle={{ backgroundColor: "hsl(var(--background))", border: "1px solid hsl(var(--border))" }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
