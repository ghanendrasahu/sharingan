import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { DocumentUpload } from "../components/DocumentUpload";
import { DocumentList } from "../components/DocumentList";
import { DocumentDetail } from "../components/DocumentDetail";
import type { Document } from "../lib/documents";

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleUploadComplete = (_documentId: string) => {
    setSelectedDocument(null);
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  const handleSelectDocument = (document: Document) => {
    setSelectedDocument(document);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-muted-foreground mt-2">
          Upload and manage your legal documents for analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Upload Document</h2>
            <DocumentUpload onUploadComplete={handleUploadComplete} />
          </div>

          <div className="border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Your Documents</h2>
            <DocumentList
              onSelectDocument={handleSelectDocument}
              selectedDocumentId={selectedDocument?.id}
            />
          </div>
        </div>

        <div className="lg:col-span-2">
          {selectedDocument ? (
            <DocumentDetail
              documentId={selectedDocument.id}
              onBack={() => setSelectedDocument(null)}
            />
          ) : (
            <div className="flex items-center justify-center h-64 border rounded-lg">
              <p className="text-muted-foreground">
                Select a document to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
