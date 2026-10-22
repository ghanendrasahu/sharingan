import { useState } from "react";
import { Search, FileText } from "lucide-react";
import { SemanticSearch } from "../components/SemanticSearch";
import { DocumentList } from "../components/DocumentList";
import { ReportsList } from "../components/ReportsList";
import { ReportDetail } from "../components/ReportDetail";
import type { Document } from "../lib/documents";
import type { Report } from "../lib/reports";

export function SearchPage() {
  const [activeTab, setActiveTab] = useState<"search" | "reports">("search");
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null
  );
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Search & Reports</h1>
        <p className="text-muted-foreground mt-2">
          Search across documents and view generated reports.
        </p>
      </div>

      <div className="flex gap-4 mb-6">
        <TabButton
          active={activeTab === "search"}
          onClick={() => setActiveTab("search")}
          icon={<Search className="h-4 w-4" />}
          label="Semantic Search"
        />
        <TabButton
          active={activeTab === "reports"}
          onClick={() => setActiveTab("reports")}
          icon={<FileText className="h-4 w-4" />}
          label="Reports"
        />
      </div>

      {activeTab === "search" ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1 border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Select Document</h2>
            <DocumentList
              onSelectDocument={setSelectedDocument}
              selectedDocumentId={selectedDocument?.id}
            />
          </div>

          <div className="lg:col-span-3">
            <div className="border rounded-lg p-4">
              <SemanticSearch />
            </div>
          </div>
        </div>
      ) : (
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
              <div className="space-y-4">
                <div className="border rounded-lg p-4">
                  <ReportsList
                    documentId={selectedDocument.id}
                    onSelectReport={setSelectedReport}
                    selectedReportId={selectedReport?.report_id}
                  />
                </div>

                {selectedReport && (
                  <div className="border rounded-lg p-4">
                    <ReportDetail
                      report={selectedReport}
                      onBack={() => setSelectedReport(null)}
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 border rounded-lg">
                <p className="text-muted-foreground">
                  Select a document to view reports
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
        active
          ? "bg-primary text-primary-foreground"
          : "bg-muted hover:bg-muted/80"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
