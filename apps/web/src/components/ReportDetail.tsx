import { FileText, AlertTriangle, CheckCircle } from "lucide-react";
import type { Report } from "../lib/reports";

interface ReportDetailProps {
  report: Report;
  onBack?: () => void;
}

export function ReportDetail({ report, onBack }: ReportDetailProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{report.title || "Report"}</h2>
          <p className="text-muted-foreground">
            {report.report_type.replace("_", " ").toUpperCase()} • Generated{" "}
            {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 border rounded-md hover:bg-muted"
          >
            Back to Reports
          </button>
        )}
      </div>

      {report.risk_summary && (
        <div className="grid grid-cols-4 gap-4">
          <RiskCard
            count={report.risk_summary.total_risks}
            label="Total Risks"
            level="all"
          />
          <RiskCard
            count={report.risk_summary.high_count}
            label="High Risk"
            level="high"
          />
          <RiskCard
            count={report.risk_summary.medium_count}
            label="Medium Risk"
            level="medium"
          />
          <RiskCard
            count={report.risk_summary.low_count}
            label="Low Risk"
            level="low"
          />
        </div>
      )}

      {report.executive_summary && (
        <div className="border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">Executive Summary</h3>
          </div>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
            {report.executive_summary}
          </p>
        </div>
      )}

      {report.sections.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-semibold">Report Sections</h3>
          {report.sections.map((section, index) => (
            <div key={index} className="border rounded-lg p-4">
              <h4 className="font-medium mb-2">{section.title}</h4>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {section.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RiskCard({
  count,
  label,
  level,
}: {
  count: number;
  label: string;
  level: string;
}) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        {level === "high" && <AlertTriangle className="h-4 w-4 text-red-500" />}
        {level === "medium" && (
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
        )}
        {level === "low" && <CheckCircle className="h-4 w-4 text-green-500" />}
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <p className="text-2xl font-bold">{count}</p>
    </div>
  );
}
