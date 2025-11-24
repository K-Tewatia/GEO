import { Button } from "@/components/ui/button";
import { SummaryMetrics } from "@/components/summary-metrics";
import { PromptsTable } from "@/components/prompts-table";
import { DualVisibilityCharts } from "@/components/dual-visibility-charts";
import { ShareOfVoiceChart } from "@/components/share-of-voice-chart";
import { DomainCitationsTable } from "@/components/domain-citations-table";
import { ReanalyzeButton } from "@/components/reanalyze-button";
import type { AnalysisResults as AnalysisResultsType } from "@shared/schema";
import { RotateCcw } from "lucide-react";

interface AnalysisResultsProps {
  results: AnalysisResultsType;
  onNewAnalysis: () => void;
  sessionId: string;
}

export function AnalysisResults({
  results,
  onNewAnalysis,
  sessionId,
}: AnalysisResultsProps) {
  // ✅ FIX: Find the score for the ACTUAL BRAND, not just the first item (which might be a competitor)
  const brandScore =
    results.brand_scores && results.brand_scores.length > 0
      ? results.brand_scores.find(
          (score) => score.brand === results.brand_name
        ) || results.brand_scores[0]  // Fallback to first if exact match not found
      : {
          brand: results.brand_name,
          mention_count: 0,
          average_position: 0,
          visibility_score: 0,
          mention_rate: 0,
          rank: 1,
        };

  const shareOfVoiceData =
    results.share_of_voice && results.share_of_voice.length > 0
      ? results.share_of_voice
      : [];

  // Use the correct key for domain data as established previously
  const domainData = results.domain_citations || [];

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      <SummaryMetrics
        totalPrompts={results.num_prompts || 0}
        mentionCount={brandScore.mention_count} 
        averagePosition={brandScore.average_position}
        visibilityScore={brandScore.visibility_score} 
      />
      
      {/* Prompts Table */}
      <PromptsTable responses={results.llm_responses || []} />

      {/* Dual Visibility Charts - Side by Side */}
      <DualVisibilityCharts
        brandName={results.brand_name}
        productName={results.product_name}
        sessionId={sessionId}
      />

      {/* Domain Citations Table & Share of Voice Chart - Side by Side */}
      <div className="grid grid-cols-2 gap-4">
        <DomainCitationsTable citations={domainData} />
        <div>
          <ShareOfVoiceChart shareOfVoice={shareOfVoiceData} />
        </div>
      </div>

      {/* Re-analyze Button & New Analysis Button */}
      <div className="space-y-2">
        <ReanalyzeButton sessionId={sessionId} onReanalyzeStart={onNewAnalysis} />
        <Button
          onClick={onNewAnalysis}
          variant="secondary"
          className="w-full"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          New Analysis
        </Button>
      </div>
    </div>
  );
}