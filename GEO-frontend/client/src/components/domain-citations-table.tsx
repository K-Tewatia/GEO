import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DomainCitation } from "@shared/schema";
import { ExternalLink } from "lucide-react";

interface DomainCitationsTableProps {
  citations: DomainCitation[];
}

export function DomainCitationsTable({ citations }: DomainCitationsTableProps) {
  const sortedCitations = [...citations].sort((a, b) => b.count - a.count);

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4" data-testid="text-table-title-domains">Top Cited Domains</h3>
      
      {sortedCitations.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <div className="text-center space-y-2">
            <ExternalLink className="h-12 w-12 mx-auto opacity-50" />
            <p>No citation data available</p>
          </div>
        </div>
      ) : (
        <div className="rounded-md border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="font-semibold">Domain</TableHead>
                <TableHead className="font-semibold text-right">Count</TableHead>
                <TableHead className="font-semibold text-right">Percentage</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCitations.map((citation, index) => (
                <TableRow key={index} data-testid={`row-domain-${index}`}>
                  <TableCell className="font-medium">
                    {citation.domain}
                  </TableCell>
                  <TableCell className="text-right">
                    {citation.count}
                  </TableCell>
                  <TableCell className="text-right">
                    {citation.percentage.toFixed(1)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </Card>
  );
}
