import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { queryClient } from "@/lib/queryClient";
import { type AnalysisStatus, type AnalysisResults } from "@shared/schema";
import { Loader2, AlertCircle } from "lucide-react";

interface AnalysisProgressProps {
  sessionId: string;
  onComplete: (results: AnalysisResults) => void;
}

export function AnalysisProgress({ sessionId, onComplete }: AnalysisProgressProps) {
  const { toast } = useToast();
  const [showError, setShowError] = useState(false);

  const { data: status, error: statusError, refetch: refetchStatus } = useQuery<AnalysisStatus>({
    queryKey: ["/api/analysis/status", sessionId],
    refetchInterval: (query) => {
      const data = query.state.data as AnalysisStatus | undefined;
      return data?.status === "completed" || showError ? false : 2000;
    },
    enabled: !!sessionId && !showError,
    retry: 3,
  });

  useEffect(() => {
    if (statusError && !showError) {
      setShowError(true);
      toast({
        title: "Connection Error",
        description: statusError.message || "Unable to connect to analysis service",
        variant: "destructive",
      });
    }
  }, [statusError, showError, toast]);

  const { data: results, error: resultsError, refetch: refetchResults } = useQuery<AnalysisResults>({
    queryKey: ["/api/results", sessionId],
    enabled: !!sessionId && status?.status === "completed" && !showError,
    retry: 3,
  });

  useEffect(() => {
    if (resultsError && !showError) {
      setShowError(true);
      toast({
        title: "Failed to Load Results",
        description: resultsError.message || "Could not retrieve analysis results",
        variant: "destructive",
      });
    }
  }, [resultsError, showError, toast]);

  useEffect(() => {
    if (results && status?.status === "completed") {
      onComplete(results);
    }
  }, [results, status, onComplete]);

  const handleRetry = async () => {
    setShowError(false);
    queryClient.removeQueries({ queryKey: ["/api/analysis/status", sessionId] });
    queryClient.removeQueries({ queryKey: ["/api/results", sessionId] });
    
    const statusResult = await refetchStatus();
    if (statusResult.data?.status === "completed") {
      await refetchResults();
    }
  };

  const progress = status?.progress ?? 0;
  const hasError = (statusError || resultsError) && showError;

  if (hasError) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-2xl p-8">
          <div className="space-y-6">
            <div className="flex items-center justify-center">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10">
                <AlertCircle className="h-8 w-8 text-destructive" />
              </div>
            </div>

            <div className="text-center space-y-2">
              <h2 className="text-2xl font-semibold">Connection Failed</h2>
              <p className="text-muted-foreground">
                Unable to connect to the analysis service. Please ensure the FastAPI backend is running and accessible.
              </p>
            </div>

            <div className="flex justify-center">
              <Button
                onClick={handleRetry}
                data-testid="button-retry"
              >
                Retry Connection
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="w-full max-w-2xl p-8">
        <div className="space-y-6">
          <div className="flex items-center justify-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
          </div>

          <div className="text-center space-y-2">
            <h2 className="text-2xl font-semibold" data-testid="text-analysis-status">
              Analyzing Brand Visibility
            </h2>
            <p className="text-muted-foreground" data-testid="text-current-step">
              {status?.current_step || "Initializing..."}
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium" data-testid="text-progress-percentage">
                {Math.round(progress)}%
              </span>
            </div>
            <Progress value={progress} className="h-3" data-testid="progress-bar" />
          </div>

          <p className="text-center text-sm text-muted-foreground">
            This may take a few minutes. We're querying multiple LLMs and analyzing the responses.
          </p>
        </div>
      </Card>
    </div>
  );
}
