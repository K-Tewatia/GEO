import { useState } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { AnalysisProgress } from "@/components/analysis-progress";
import { AnalysisResults } from "@/components/analysis-results";
import type { AnalysisResults as AnalysisResultsType } from "@shared/schema";
import { useToast } from "@/hooks/use-toast";

type ViewState = "form" | "loading" | "results";

export default function Home() {
  const { toast } = useToast();
  const [viewState, setViewState] = useState<ViewState>("form");
  const [sessionId, setSessionId] = useState<string>("");
  const [results, setResults] = useState<AnalysisResultsType | null>(null);

  const handleAnalysisStart = (newSessionId: string) => {
    setSessionId(newSessionId);
    setViewState("loading");
  };

  const handleAnalysisComplete = (analysisResults: AnalysisResultsType) => {
    setResults(analysisResults);
    setViewState("results");
  };

  // ✅ NEW: Handle recent analysis selection
  const handleRecentAnalysisSelect = async (selectedSessionId: string) => {
    setSessionId(selectedSessionId);
    setViewState("loading");

    try {
      console.log(`Loading recent analysis: ${selectedSessionId}`);
      const response = await fetch(`/api/results/${selectedSessionId}`);

      if (!response.ok) {
        throw new Error("Failed to load analysis");
      }

      const analysisResults: AnalysisResultsType = await response.json();
      console.log("✅ Analysis loaded successfully");

      handleAnalysisComplete(analysisResults);
    } catch (error) {
      console.error("Error loading recent analysis:", error);
      toast({
        title: "Failed to Load Analysis",
        description:
          error instanceof Error
            ? error.message
            : "Could not load the selected analysis. Please try again.",
        variant: "destructive",
      });
      setViewState("form");
    }
  };

  const handleNewAnalysis = () => {
    setViewState("form");
    setSessionId("");
    setResults(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {viewState === "form" && (
          <div className="space-y-6">
            {/* Header */}
            <div className="text-center space-y-2">
              <h1 className="text-4xl font-bold tracking-tight">Brand Visibility Analyzer</h1>
              <p className="text-lg text-muted-foreground">
                Analyze your brand's visibility across search engines and LLMs
              </p>
            </div>

            {/* Form with Recent Analyses */}
            <AnalysisForm
              onAnalysisStart={handleAnalysisStart}
              onRecentAnalysisSelect={handleRecentAnalysisSelect} // ✅ ADD THIS
            />
          </div>
        )}

        {viewState === "loading" && (
          <AnalysisProgress
            sessionId={sessionId}
            onComplete={handleAnalysisComplete}
          />
        )}

        {viewState === "results" && results && (
          <AnalysisResults
            results={results}
            onNewAnalysis={handleNewAnalysis}
          />
        )}
      </div>
    </div>
  );
}
