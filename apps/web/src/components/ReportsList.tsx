import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Download,
  Trash2,
  Clock,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { reportsApi, type Report } from "../lib/reports";

interface ReportsListProps {
  documentId: string;
  onSelectReport?: (report: Report) => void;
  selectedReportId?: string;
}

export function ReportsList({
  documentId,
  onSelectReport,
  selectedReportId,
}: ReportsListProps) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["reports", documentId],
    queryFn: () => reportsApi.listReports(documentId),
  });

  const deleteMutation = useMutation({
    mutationFn: reportsApi.deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", documentId] });
    },
  });

  const handleDelete = (reportId: string) => {
    if (confirm("Are you sure you want to delete this report?")) {
      deleteMutation.mutate(reportId);
    }
  };

  const handleExport = async (reportId: string, format: string) => {
    const result = await reportsApi.exportReport(
      reportId,
      format as "json" | "html" | "markdown"
    );
    const blob = new Blob([result.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `report-${reportId}.${format}`;
    window.document.body.appendChild(a);
    a.click();
    window.document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-muted-foreground">Loading reports...</div>
      </div>
    );
  }

  const reports = data?.reports || [];

  if (reports.length === 0) {
    return (
      <div className="text-center py-8 border rounded-lg">
        <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No reports generated yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {reports.map((report) => (
        <ReportCard
          key={report.report_id}
          report={report}
          isSelected={selectedReportId === report.report_id}
          onClick={() => onSelectReport?.(report)}
          onDelete={() => handleDelete(report.report_id)}
          onExport={(format) => handleExport(report.report_id, format)}
        />
      ))}
    </div>
  );
}

function ReportCard({
  report,
  isSelected,
  onClick,
  onDelete,
  onExport,
}: {
  report: Report;
  isSelected: boolean;
  onClick: () => void;
  onDelete: () => void;
  onExport: (format: string) => void;
}) {
  return (
    <div
      className={`border rounded-lg p-3 cursor-pointer hover:bg-muted/50 transition-colors ${
        isSelected ? "border-primary bg-primary/5" : ""
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 mb-2">
        <FileText className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium">{report.title || "Report"}</span>
      </div>

      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-muted-foreground">
          {report.report_type}
        </span>
        <span className="text-xs text-muted-foreground">•</span>
        <span className="text-xs text-muted-foreground flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {new Date(report.generated_at).toLocaleDateString()}
        </span>
      </div>

      {report.risk_summary && (
        <div className="flex items-center gap-2 mb-2">
          <RiskBadge level={report.risk_summary.risk_level} />
          <span className="text-xs text-muted-foreground">
            {report.risk_summary.total_risks} risks found
          </span>
        </div>
      )}

      <div className="flex items-center gap-1 mt-2">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onExport("json");
          }}
          className="p-1.5 hover:bg-muted rounded text-xs"
        >
          <Download className="h-3 w-3" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onExport("html");
          }}
          className="p-1.5 hover:bg-muted rounded text-xs"
        >
          HTML
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1.5 hover:bg-muted rounded text-red-500"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-green-100 text-green-800",
  };

  const icons: Record<string, React.ReactNode> = {
    high: <AlertTriangle className="h-3 w-3" />,
    medium: <AlertTriangle className="h-3 w-3" />,
    low: <CheckCircle className="h-3 w-3" />,
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full flex items-center gap-1 ${
        styles[level] || "bg-gray-100 text-gray-800"
      }`}
    >
      {icons[level]}
      {level}
    </span>
  );
}
