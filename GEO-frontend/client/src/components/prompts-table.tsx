import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { LLMResponse } from "@shared/schema";
import { ChevronLeft, ChevronRight, Search, ChevronDown, Link2, Eye } from "lucide-react";

interface PromptsTableProps {
  responses: LLMResponse[];
}

const ITEMS_PER_PAGE = 10;

export function PromptsTable({ responses }: PromptsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const filteredResponses = useMemo(() => {
    if (!searchTerm) return responses;
    const term = searchTerm.toLowerCase();
    return responses.filter(
      (r) =>
        r.prompt?.toLowerCase().includes(term) ||
        r.llm_name?.toLowerCase().includes(term) ||
        r.llm_model?.toLowerCase().includes(term) ||
        r.model_name?.toLowerCase().includes(term) ||
        r.response?.toLowerCase().includes(term)
    );
  }, [responses, searchTerm]);

  const totalPages = Math.ceil(filteredResponses.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentResponses = filteredResponses.slice(startIndex, endIndex);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(Math.max(1, Math.min(newPage, totalPages)));
  };

  const toggleRowExpanded = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  // ✅ FIXED: Helper to get proper source display name
  const getSourceName = (response: LLMResponse): string => {
    return response.llm_name || response.llm_model || response.model_name || "Unknown";
  };

  // ✅ FIXED: Helper to ensure citations are properly parsed
  const getCitations = (response: LLMResponse): string[] => {
    if (!response.citations) return [];
    
    // Handle both array and string formats
    if (typeof response.citations === "string") {
      try {
        return JSON.parse(response.citations);
      } catch {
        return [];
      }
    }
    
    if (Array.isArray(response.citations)) {
      return response.citations.filter(c => c && typeof c === "string");
    }
    
    return [];
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Analyzed Prompts</h3>
      
      <div className="relative mb-4">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search prompts, sources..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setCurrentPage(1);
          }}
          className="pl-9"
          data-testid="input-search-prompts"
        />
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Prompt</TableHead>
              {/* ✅ FIXED: Changed header to "Source (LLM)" to be more explicit */}
              <TableHead>Source (LLM)</TableHead>
              <TableHead>Citations</TableHead>
              <TableHead>Avg Visibility Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currentResponses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                  {searchTerm ? "No results found" : "No prompts analyzed yet"}
                </TableCell>
              </TableRow>
            ) : (
              currentResponses.map((response, index) => {
                const citations = getCitations(response);
                const sourceName = getSourceName(response);
                
                return (
                  <TableRow key={index}>
                    {/* Prompt */}
                    <TableCell className="max-w-xs">
                      <div className="line-clamp-2">{response.prompt || "—"}</div>
                    </TableCell>

                    {/* ✅ FIXED: Source displays LLM name, not prompt */}
                    <TableCell>
                      <Badge variant="outline">{sourceName}</Badge>
                    </TableCell>

                    {/* Citations Dropdown */}
                    <TableCell>
                      {citations && citations.length > 0 ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="gap-2">
                              <Link2 className="h-4 w-4" />
                              {citations.length} Citations
                              <ChevronDown className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="max-w-md">
                            {citations.map((citation, citationIndex) => (
                              <DropdownMenuItem
                                key={citationIndex}
                                onClick={() => window.open(citation, "_blank")}
                                className="cursor-pointer truncate"
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                <span className="truncate text-xs">{citation}</span>
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <Badge variant="secondary">No sources</Badge>
                      )}
                    </TableCell>

                    {/* Avg Visibility Score */}
                    <TableCell>
                      {response.visibility_score !== undefined && response.visibility_score !== null
                        ? `${response.visibility_score.toFixed(1)}%`
                        : "—"}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <span className="text-sm text-gray-600">
            Showing {startIndex + 1} to {Math.min(endIndex, filteredResponses.length)} of{" "}
            {filteredResponses.length} results
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              data-testid="button-previous-page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              data-testid="button-next-page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
