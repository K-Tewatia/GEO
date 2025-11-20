// fileName: App.tsx (FIXED)

import { useState, useEffect } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { AnalysisResults } from "@/components/analysis-results";
import { BrandSelector } from "@/components/brand-selector";
import { RecentAnalysesSidebar } from "@/components/recent-analyses-sidebar";
// ✅ CRITICAL FIX: Import the correct progress component
import { AnalysisProgress } from "@/components/analysis-progress"; 
import type { AnalysisResults as AnalysisResultsType } from "@shared/schema";
import type { AnalysisSession } from "@shared/schema";


const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] =
    useState<AnalysisResultsType | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  // Tracks when we are actively fetching old results
  const [isFetchingResults, setIsFetchingResults] = useState(false); 

  // Handler for starting a new analysis
  const handleAnalysisStart = (sessionId: string) => { 
    setSelectedSessionId(sessionId); 
    setIsAnalyzing(true);
    setAnalysisResults(null);
    setIsFetchingResults(false);
  };

  // Handler for selecting an existing analysis from the sidebar or recent list
  // Handler for selecting an existing analysis from the sidebar or recent list
  const handleAnalysisSelect = (sessionId: string, analysis: AnalysisSession | null = null) => {
    // 1. Reset states
    setAnalysisResults(null);
    setIsAnalyzing(false);
    
    // 2. Set the new ID (this will trigger the useEffect hook below)
    setSelectedSessionId(sessionId);
    
    // 3. Update the brand if the selection came from the list/sidebar
    // ✅ FIX: Use snake_case property from backend
    if (analysis && analysis.brand_name && analysis.brand_name !== selectedBrand) {
      setSelectedBrand(analysis.brand_name);
    }
  };


  // Handler for starting a completely new session (clears everything)
  const handleNewAnalysis = () => {
    setAnalysisResults(null);
    setSelectedSessionId(null);
    setIsAnalyzing(false);
    setIsFetchingResults(false);
  };

  // Handler called when AnalysisProgress completes a new run
  const handleResultsReady = (results: AnalysisResultsType) => {
    setAnalysisResults(results);
    setIsAnalyzing(false);
    setIsFetchingResults(false);
  };
  
  // ----------------------------------------------------
  // CRITICAL FIX: useEffect to fetch results when an old session is selected
  // ----------------------------------------------------
  useEffect(() => {
    // Condition: A session is selected, we are not actively analyzing a new job, 
    // and we haven't loaded results for this session yet.
    if (selectedSessionId && !isAnalyzing && !analysisResults) {
      setIsFetchingResults(true);

      const fetchExistingResults = async () => {
        try {
          // Poll the results endpoint directly
          const resultsUrl = `${API_BASE_URL}/api/results/${selectedSessionId}`;
          const statusUrl = `${API_BASE_URL}/api/analysis/status/${selectedSessionId}`;
          
          const response = await fetch(resultsUrl);
          
          if (!response.ok) {
            // If the results endpoint fails, check the status endpoint.
            const statusResponse = await fetch(statusUrl);
            const statusData = await statusResponse.json();
            
            if (statusData.status === 'running') {
                // If it's still running, switch to the AnalysisProgress component view
                setIsAnalyzing(true);
                setIsFetchingResults(false);
                return;
            }
            
            // If status is 'completed' or 'error', proceed to throw the error
            throw new Error(`Failed to load results (Status: ${response.status})`);
          }
          
          const results: AnalysisResultsType = await response.json();
          setAnalysisResults(results); // Update state to render AnalysisResults
        } catch (error) {
          console.error("Error fetching previous analysis results:", error);
          // Keep analysisResults as null to indicate failure
          setAnalysisResults(null); 
        } finally {
          setIsFetchingResults(false);
          setIsAnalyzing(false); // Ensure we exit analyzing mode if we hit an error
        }
      };

      fetchExistingResults();
    }
  }, [selectedSessionId, isAnalyzing, analysisResults]); 

  // ----------------------------------------------------
  // Component Render
  // ----------------------------------------------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Brand Visibility Analyzer
          </h1>
          <p className="text-slate-600">
            Track and analyze your brand's online presence
          </p>
        </header>

        <div className="grid grid-cols-4 gap-6">
          {/* Left Sidebar - Brand Selector & Recent Analyses */}
          <div className="col-span-1 space-y-4 h-fit sticky top-6">
            <div>
              <h2 className="text-sm font-semibold mb-2 text-slate-700">
                Select Brand
              </h2>
              <BrandSelector
                selectedBrand={selectedBrand}
                onBrandSelect={setSelectedBrand}
              />
            </div>

            {selectedBrand && (
              <div>
                <h2 className="text-sm font-semibold mb-2 text-slate-700">
                  History
                </h2>
                <RecentAnalysesSidebar
                  selectedBrand={selectedBrand}
                  selectedSessionId={selectedSessionId}
                  onSelectAnalysis={handleAnalysisSelect}
                />
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <div className="col-span-3">
            {/* 1. New Analysis in Progress */}
            {isAnalyzing && selectedSessionId && !analysisResults && (
              <AnalysisProgress
                sessionId={selectedSessionId}
                onComplete={handleResultsReady} 
              />
            )}
            
            {/* 2. Fetching Old Results */}
            {isFetchingResults && !isAnalyzing && (
                 <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="text-center space-y-4">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                        <p className="text-lg text-gray-500">Loading historical results...</p>
                    </div>
                 </div>
            )}

            {/* 3. Show Form (Initial state or reset) */}
            {!isAnalyzing && !isFetchingResults && !analysisResults && (
              <AnalysisForm
                onAnalysisStart={handleAnalysisStart}
                // When selecting a recent analysis from the form tab, use the same handler
                onRecentAnalysisSelect={(sessionId) => {
                    // Pass null for analysis, as the list item doesn't have the full AnalysisSession type here
                    handleAnalysisSelect(sessionId, null); 
                }}
              />
            )}

            {/* 4. Show Results (after completion or successful historical load) */}
            {analysisResults && selectedSessionId && (
              <AnalysisResults
                results={analysisResults}
                onNewAnalysis={handleNewAnalysis}
                sessionId={selectedSessionId}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}