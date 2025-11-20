import { Card } from "@/components/ui/card";
import { FileText, Hash, TrendingUp, Eye } from "lucide-react";

interface SummaryMetricsProps {
  totalPrompts: number;
  mentionCount: number;
  averagePosition: number;
  visibilityScore: number;
}

const metrics = [
  {
    icon: FileText,
    label: "Analyzed Prompts",
    key: "totalPrompts",
    color: "text-blue-600 bg-blue-100",
    testId: "metric-total-prompts",
  },
  {
    icon: Hash,
    label: "Brand Mentions",
    key: "mentionCount",
    color: "text-green-600 bg-green-100",
    testId: "metric-mention-count",
  },
  {
    icon: TrendingUp,
    label: "Average Position",
    key: "averagePosition",
    color: "text-purple-600 bg-purple-100",
    testId: "metric-average-position",
    // FIX: Safely handle null/undefined/NaN
    format: (val: number | null | undefined) => {
      if (val === null || val === undefined || isNaN(val)) return "—";
      return val.toFixed(1);
    },
  },
  {
    icon: Eye,
    label: "Average Visibility",
    key: "visibilityScore",
    color: "text-orange-600 bg-orange-100",
    testId: "metric-visibility-score",
    // FIX: Safely handle null/undefined/NaN
    format: (val: number | null | undefined) => {
      if (val === null || val === undefined || isNaN(val)) return "0.0%";
      return `${val.toFixed(1)}%`;
    },
  },
] as const;

export function SummaryMetrics({
  totalPrompts,
  mentionCount,
  averagePosition,
  visibilityScore,
}: SummaryMetricsProps) {
  // Create a safe values object
  const values = {
    totalPrompts: totalPrompts || 0,
    mentionCount: mentionCount || 0,
    averagePosition, // Allow null here so format function can handle it
    visibilityScore, // Allow null here so format function can handle it
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        // @ts-ignore - iterating over keys is safe here given the const array structure
        const value = values[metric.key];
        
        // FIX: Robust check for format function existence
        const displayValue = 'format' in metric 
          ? metric.format(value) 
          : (value !== null && value !== undefined ? value : 0);

        return (
          <Card key={metric.key} className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2 flex-1">
                <p className="text-sm font-medium text-muted-foreground">
                  {metric.label}
                </p>
                <p
                  className="text-3xl font-bold"
                  data-testid={metric.testId}
                >
                  {displayValue}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${metric.color}`}>
                <Icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}