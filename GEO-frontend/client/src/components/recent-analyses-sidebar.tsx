import { Card } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { Calendar, Package } from "lucide-react";
import { Loader2 } from "lucide-react";
import type { AnalysisSession } from "@shared/schema";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface RecentAnalysesSidebarProps {
  selectedBrand: string | null;
  onSelectAnalysis: (sessionId: string, analysis: AnalysisSession) => void; 
  selectedSessionId: string | null;
}


export function RecentAnalysesSidebar({
  selectedBrand,
  onSelectAnalysis,
  selectedSessionId,
}: RecentAnalysesSidebarProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["recent-analyses", selectedBrand],
    queryFn: async () => {
      if (!selectedBrand) return { sessions: [] };
      
      const response = await fetch(
        `${API_BASE_URL}/api/recent-analyses-by-brand/${encodeURIComponent(selectedBrand)}`
      );
      
      if (!response.ok) throw new Error("Failed to fetch analyses");
      return response.json();
    },
    enabled: !!selectedBrand,
    staleTime: 1000 * 60,
  });

  if (!selectedBrand) {
    return (
      <Card className="p-4 h-full flex items-center justify-center text-gray-500">
        <p className="text-sm">Select a brand to view analyses</p>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="p-4 flex items-center justify-center h-96">
        <Loader2 className="h-4 w-4 animate-spin" />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 text-red-500 h-96">
        <p className="text-sm">Error loading analyses</p>
      </Card>
    );
  }

  const sessions: AnalysisSession[] = data?.sessions || [];

  return (
    <Card className="h-96 p-3 overflow-y-auto border">
      <h3 className="font-semibold mb-3 text-sm">Recent Analyses</h3>
      {sessions.length === 0 ? (
        <p className="text-xs text-gray-500">No analyses for this brand</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <button
              key={session.session_id}
              onClick={() => onSelectAnalysis(session.session_id, session)}
              className={`w-full text-left p-2 rounded border transition text-xs ${
                selectedSessionId === session.session_id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  {/* ✅ FIX: Use snake_case property from backend */}
                  <p className="text-xs font-medium truncate">{session.brand_name}</p>
                  {session.product_name && (
                    <p className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                      <Package className="h-3 w-3" />
                      {session.product_name}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(session.timestamp).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </Card>
  );
}
