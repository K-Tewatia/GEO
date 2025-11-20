import { Card } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertTriangle } from "lucide-react";

// Robust API URL definition
const API_BASE_URL = window.location.origin.includes('localhost') 
    ? "http://localhost:8000" 
    : window.location.origin;

interface DualVisibilityChartsProps {
  brandName: string;
  productName?: string;
  sessionId: string;
}

interface ChartDataPoint {
  date: string;
  visibility: number;
  timestamp: string;
}

export function DualVisibilityCharts({
  brandName,
  productName,
  sessionId,
}: DualVisibilityChartsProps) {
  
  // Determine if this is a product-specific analysis
  const isProductSpecific = !!productName && productName.trim().length > 0;

  // 1. Fetch Main Visibility History
  const { 
    data: mainHistoryData, 
    isLoading: mainLoading,
    isError: mainError 
  } = useQuery({
    queryKey: ["main-visibility-history", brandName, productName, isProductSpecific],
    queryFn: async () => {
      const endpoint = isProductSpecific
        ? `${API_BASE_URL}/api/visibility-history/brand-product/${encodeURIComponent(brandName)}/${encodeURIComponent(productName)}`
        : `${API_BASE_URL}/api/brand-history/${encodeURIComponent(brandName)}`;

      const response = await fetch(endpoint);
      
      if (!response.ok) {
        if (response.status === 404) return { history: [] };
        // This error will now be caught by the UI
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }
      
      const data = await response.json();

      // Standardize to 'visibility'
      const formattedHistory = (data.history || []).map((item: any) => ({
        date: item.date,
        timestamp: item.timestamp,
        visibility: Number(item.visibility !== undefined ? item.visibility : item.visibility_score || 0)
      }));

      return { ...data, history: formattedHistory };
    },
  });

  // 2. Fetch Same Prompts Visibility History
  const { 
    data: samePromptsData, 
    isLoading: samePromptsLoading,
    isError: samePromptsError 
  } = useQuery({
    queryKey: ["same-prompts-history", sessionId],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/same-prompts-history/${sessionId}`
      );
      if (!response.ok) throw new Error("Failed to fetch same prompts history");
      
      const data = await response.json();

      const formattedHistory = (data.history || []).map((item: any) => ({
        date: item.date,
        timestamp: item.timestamp,
        visibility: Number(item.visibility !== undefined ? item.visibility : item.visibility_score || 0)
      }));

      return { ...data, history: formattedHistory };
    },
  });

  const mainHistory: ChartDataPoint[] = mainHistoryData?.history || [];
  const samePromptsHistory: ChartDataPoint[] = samePromptsData?.history || [];

  const isLoading = mainLoading || samePromptsLoading;

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 flex items-center justify-center h-80">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </Card>
        <Card className="p-6 flex items-center justify-center h-80">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </Card>
      </div>
    );
  }

  // Helper to render charts with Error Handling
  const renderChart = (data: ChartDataPoint[], title: string, lineColor: string, isError: boolean) => (
    <Card className="p-4">
      <h3 className="font-semibold text-sm mb-4">{title}</h3>
      
      {isError ? (
        <div className="flex items-center justify-center h-64 text-red-500 text-sm bg-red-50 rounded-md border border-red-100">
          <div className="text-center p-4">
            <AlertTriangle className="h-6 w-6 mx-auto mb-2" />
            <p>Failed to load chart data.</p>
            <p className="text-xs mt-1">Check backend logs.</p>
          </div>
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-gray-500 text-sm bg-slate-50 rounded-md border border-dashed">
          <div className="text-center p-4">
            <p>No historical data available yet.</p>
            <p className="text-xs mt-1">Run more analyses to see trends.</p>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
             <XAxis 
              dataKey="date" 
              style={{ fontSize: '10px' }} 
              tick={{ fill: '#666' }} 
              tickMargin={10}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis
              domain={[0, 100]}
              style={{ fontSize: "11px" }}
              tick={{ fill: "#666" }}
              label={{ value: "Visibility %", angle: -90, position: "insideLeft", style: { fontSize: '12px', fill: '#666' } }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(255, 255, 255, 0.98)",
                border: "1px solid #e2e8f0",
                borderRadius: "6px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                fontSize: "12px"
              }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, "Visibility"]}
            />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
            <Line
              type="monotone"
              dataKey="visibility"
              stroke={lineColor}
              dot={{ fill: lineColor, r: 4, strokeWidth: 0 }}
              activeDot={{ r: 6, strokeWidth: 0 }}
              strokeWidth={2.5}
              name="Visibility Score"
              animationDuration={1000}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );

  const mainChartTitle = isProductSpecific
    ? `${brandName} + ${productName} Visibility`
    : `${brandName} Visibility History`;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {renderChart(
        mainHistory,
        mainChartTitle,
        "hsl(var(--primary))",
        mainError // Pass error state
      )}
      
      {renderChart(
        samePromptsHistory,
        "Same Prompts Re-analysis Trend",
        "#8b5cf6",
        samePromptsError // Pass error state
      )}
    </div>
  );
}
