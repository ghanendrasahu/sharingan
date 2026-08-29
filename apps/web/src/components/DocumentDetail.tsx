import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Calendar,
  HardDrive,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import { documentsApi } from "../lib/documents";

interface DocumentDetailProps {
  documentId: string;
  onBack?: () => void;
}

export function DocumentDetail({ documentId, onBack }: DocumentDetailProps) {
  const {
    data: document,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => documentsApi.get(documentId),
    refetchInterval: (query) => {
      if (query.state.data?.status === "processing") {
        return 2000;
      }
      return false;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading document...</div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Failed to load document</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        {onBack && (
          <button onClick={onBack} className="p-2 hover:bg-muted rounded">
            <ArrowLeft className="h-5 w-5" />
          </button>
        )}
        <h2 className="text-2xl font-bold">{document.name}</h2>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card title="File Information">
          <div className="space-y-3">
            <InfoRow
              icon={<FileText className="h-4 w-4" />}
              label="Type"
              value={document.file_type.toUpperCase()}
            />
            <InfoRow
              icon={<HardDrive className="h-4 w-4" />}
              label="Size"
              value={`${(document.file_size / 1024).toFixed(1)} KB`}
            />
            <InfoRow
              icon={<Calendar className="h-4 w-4" />}
              label="Uploaded"
              value={new Date(document.created_at).toLocaleString()}
            />
            <InfoRow
              icon={<Calendar className="h-4 w-4" />}
              label="Updated"
              value={new Date(document.updated_at).toLocaleString()}
            />
          </div>
        </Card>

        <Card title="Processing Status">
          <div className="space-y-3">
            <StatusBadge status={document.status} />
            {document.status === "processing" && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Processing document...
              </div>
            )}
            {document.status === "completed" && (
              <p className="text-sm text-green-600">
                Document processed successfully. Ready for analysis.
              </p>
            )}
            {document.status === "failed" && (
              <div className="space-y-2">
                <p className="text-sm text-red-600">
                  Document processing failed.
                </p>
                <button
                  onClick={() => refetch()}
                  className="text-sm text-primary hover:underline"
                >
                  Retry processing
                </button>
              </div>
            )}
          </div>
        </Card>
      </div>

      {document.status === "completed" && (
        <Card title="Actions">
          <div className="flex gap-4">
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
              Run Analysis
            </button>
            <button className="px-4 py-2 border rounded-md hover:bg-muted">
              View Analysis History
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border rounded-lg p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-4">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{icon}</span>
      <span className="text-sm text-muted-foreground">{label}:</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    uploaded: "bg-blue-100 text-blue-800",
    processing: "bg-yellow-100 text-yellow-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`px-3 py-1 text-sm font-medium rounded-full ${
        styles[status] || "bg-gray-100 text-gray-800"
      }`}
    >
      {status}
    </span>
  );
}
