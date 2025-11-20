import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { analysisRequestSchema, AVAILABLE_LLMS, type AnalysisRequest } from "@shared/schema";
import { Loader2, Sparkles, History } from "lucide-react";
import { RecentAnalysesList } from "@/components/recent-analyses-list";

interface AnalysisFormProps {
  onAnalysisStart: (sessionId: string) => void;
  onRecentAnalysisSelect?: (sessionId: string) => void;
}

export function AnalysisForm({ onAnalysisStart, onRecentAnalysisSelect }: AnalysisFormProps) {
  const { toast } = useToast();
  const form = useForm({
    resolver: zodResolver(analysisRequestSchema),
    defaultValues: {
      brand_name: "",
      product_description: "",
      industry: "",
      website_url: "",
      num_prompts: 10,
      selected_llms: [],
    },
  });

  const startAnalysisMutation = useMutation({
    mutationFn: async (data: AnalysisRequest) => {
      const response = await apiRequest("POST", "/api/analysis/run", data);
      return await response.json();
    },
    onSuccess: (data: { session_id: string }) => {
      onAnalysisStart(data.session_id);
    },
    onError: (error: Error) => {
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to start analysis. Please try again.",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: AnalysisRequest) => {
    startAnalysisMutation.mutate(data);
  };

  const selectedLLMs = form.watch("selected_llms");
  const isFormValid = form.watch("brand_name").length > 0 && selectedLLMs.length > 0;

  return (
    <div className="w-full max-w-4xl mx-auto">
      <Tabs defaultValue="new" className="w-full">
        {/* ✅ TAB HEADERS */}
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="new" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            New Analysis
          </TabsTrigger>
          <TabsTrigger value="recent" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Recent Analyses
          </TabsTrigger>
        </TabsList>

        {/* ✅ NEW ANALYSIS TAB */}
        <TabsContent value="new" className="space-y-6 mt-6">
          <Card className="p-6 space-y-6">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Brand Name - Full Width */}
                <FormField
                  control={form.control}
                  name="brand_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-base font-semibold">Brand Name *</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter brand name (e.g., Nike, Apple, Tesla)"
                          {...field}
                          className="h-10"
                          disabled={startAnalysisMutation.isPending}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Product Description - Left Column */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={form.control}
                    name="product_description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Product Description</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Brief product/service description"
                            {...field}
                            className="h-10"
                            disabled={startAnalysisMutation.isPending}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Industry - Right Column */}
                  <FormField
                    control={form.control}
                    name="industry"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Industry</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="e.g., Tech, Fashion, Automotive"
                            {...field}
                            className="h-10"
                            disabled={startAnalysisMutation.isPending}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                {/* Website URL - Full Width */}
                <FormField
                  control={form.control}
                  name="website_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Website URL</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="https://example.com"
                          {...field}
                          className="h-10"
                          disabled={startAnalysisMutation.isPending}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* LLM Selection */}
                <FormField
                  control={form.control}
                  name="selected_llms"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-base font-semibold">Select LLMs to Analyze *</FormLabel>
                      <div className="space-y-3">
                        {AVAILABLE_LLMS.map((llm) => (
                          <div key={llm} className="flex items-center space-x-2">
                            <Checkbox
                              id={`llm-${llm}`}
                              checked={field.value?.includes(llm)}
                              onCheckedChange={(checked) => {
                                const newValue = checked
                                  ? [...(field.value || []), llm]
                                  : (field.value || []).filter((l) => l !== llm);
                                field.onChange(newValue);
                              }}
                              disabled={startAnalysisMutation.isPending}
                              data-testid={`checkbox-llm-${llm.toLowerCase().replace(/\s+/g, "-")}`}
                            />
                            <Label
                              htmlFor={`llm-${llm}`}
                              className="font-medium cursor-pointer"
                            >
                              {llm}
                            </Label>
                          </div>
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Submit Button */}
                <div className="pt-4">
                  <Button
                    type="submit"
                    size="lg"
                    className="w-full h-11 text-base font-semibold"
                    disabled={!isFormValid || startAnalysisMutation.isPending}
                  >
                    {startAnalysisMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Starting Analysis...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Start Analysis
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Form>
          </Card>
        </TabsContent>

        {/* ✅ RECENT ANALYSES TAB */}
        <TabsContent value="recent" className="mt-6">
          <Card className="p-6">
            <RecentAnalysesList
              onAnalysisSelect={(sessionId, brandName) => {
                console.log(`Loading recent analysis: ${brandName} (${sessionId})`);
                if (onRecentAnalysisSelect) {
                  onRecentAnalysisSelect(sessionId);
                }
              }}
            />
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}