import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DocumentList } from "../components/DocumentList";
import { AnalysisDashboard } from "../components/AnalysisDashboard";
import type { Document } from "../lib/documents";

const queryClient = new QueryClient();

export function AnalysisPage() {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null
  );

  return (
    <QueryClientProvider client={queryClient}>
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Analysis Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Select a document to run AI-powered analysis and get insights.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1 border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Select Document</h2>
            <DocumentList
              onSelectDocument={setSelectedDocument}
              selectedDocumentId={selectedDocument?.id}
            />
          </div>

          <div className="lg:col-span-3">
            {selectedDocument ? (
              <AnalysisDashboard documentId={selectedDocument.id} />
            ) : (
              <div className="flex items-center justify-center h-64 border rounded-lg">
                <p className="text-muted-foreground">
                  Select a document to view analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}
