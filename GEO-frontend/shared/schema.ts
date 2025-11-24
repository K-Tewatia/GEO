import { z } from "zod";

// Analysis Request Schema
export const analysisRequestSchema = z.object({
  brand_name: z.string().min(1, "Brand name is required"),
  product_name: z.string().optional(),
  industry: z.string().optional(),
  website_url: z.string().url().optional().or(z.literal("")),
  num_prompts: z.number().int().min(1).max(50).default(10),
  selected_llms: z.array(z.string()).min(1, "Select at least one LLM"),
});

export type AnalysisRequest = z.infer<typeof analysisRequestSchema>;

// Analysis Status Schema
export const analysisStatusSchema = z.object({
  session_id: z.string(),
  status: z.enum(["running", "completed", "error"]),
  progress: z.number().min(0).max(100),
  current_step: z.string(),
  error: z.string().optional(),
});

export type AnalysisStatus = z.infer<typeof analysisStatusSchema>;

// Available LLMs
export const AVAILABLE_LLMS = [
  "Claude",
  "Mistral",
  "Google AI Overview",
  "ChatGPT",
  "Perplexity",
  "Gemini",
] as const;

// LLM Response Interface
export interface LLMResponse {
  llm_name?: string;
  llm_model: string;
  prompt: string;
  response: string;
  response_length: number;
  model_name: string;
  citations?: string[]; // Citations array
  visibility_score?: number; // Visibility score if calculated
}

// Brand Score Interface
export interface BrandScore {
  brand: string;
  visibility_score: number;
  mention_count: number;
  mention_rate: number;
  average_position: number;
  rank: number;
}

// Share of Voice Interface
export interface ShareOfVoice {
  brand: string;
  percentage: number;
  mention_count: number;
}

// Domain Citation Interface
export interface DomainCitation {
  domain: string;
  citation_count: number;
  percentage: number;
}

// Model Usage Interface
export interface ModelUsage {
  model: string;
  count: number;
  percentage: number;
}

// Market Research Interface
export interface MarketResearch {
  industry: string;
  market_size: string;
  key_trends: string[];
  target_audience: string;
}

// Keywords Interface
export interface Keywords {
  primary_keywords: string[];
  secondary_keywords: string[];
  competitor_keywords: string[];
}

// Competitor Interface
export interface Competitor {
  name: string;
}

// Metrics Interface
export interface Metrics {
  total_prompts: number;
  total_responses: number;
  average_response_length: number;
  highest_mention_score: number;
  lowest_mention_score: number;
  session_duration: string;
}

// Analysis Session Interface
export interface AnalysisSession {
  session_id: string;
  brand_name: string;
  product_name?: string;
  website_url?: string;
  timestamp: string;
}


// Analysis Results Interface (main response structure)
export interface AnalysisResults {
  session_id: string;
  brand_name: string;
  product_name: string;
  industry: string;
  website_url: string;
  num_prompts: number;
  selected_llms: string[];
  created_at: string;
  status: string;
  brand_scores: BrandScore[];
  share_of_voice: ShareOfVoice[];
  domain_citations: DomainCitation[];
  llm_responses: LLMResponse[];
  model_usage: ModelUsage[];
  market_research: MarketResearch;
  keywords: Keywords;
  competitors: Competitor[];
  metrics: Metrics;
}

// Visibility History Point Interface (for charts)
export interface VisibilityHistoryPoint {
  date: string;       // e.g., '2025-11-18'
  visibility: number; // percentage
  timestamp: string;
}

// Reanalyze API response interface
export interface ReanalyzeResponse {
  new_session_id: string;
  message: string;
  status: "processing" | "error" | "completed";
}

// Brands List API response
export interface BrandsListResponse {
  brands: string[];
}

// Recent Analyses by Brand API response
export interface RecentAnalysesByBrandResponse {
  sessions: AnalysisSession[];
}

// Same Prompts History API response
export interface SamePromptsHistoryResponse {
  history: VisibilityHistoryPoint[];
  message?: string;
  error?: string;
}
