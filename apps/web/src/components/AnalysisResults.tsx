import { FileText, Users, Calendar, BookOpen } from "lucide-react";
import type { AnalysisResult } from "../lib/analysis";

interface AnalysisResultsProps {
  result: AnalysisResult;
}

export function AnalysisResults({ result }: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        <SummaryCard result={result} />
        <KeyTermsCard keyTerms={result.key_terms} />
      </div>

      <RisksList risks={result.risks} />
    </div>
  );
}

function SummaryCard({ result }: { result: AnalysisResult }) {
  const summary = result.summary;

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Executive Summary</h3>
      </div>

      {summary ? (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {summary.executive_summary}
          </p>

          {summary.key_points.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Key Points</h4>
              <ul className="list-disc list-inside text-sm space-y-1">
                {summary.key_points.map((point, i) => (
                  <li key={i} className="text-muted-foreground">
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center gap-4 text-sm">
            {summary.parties_involved.length > 0 && (
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span>{summary.parties_involved.join(", ")}</span>
              </div>
            )}
            {summary.effective_date && (
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>Effective: {summary.effective_date}</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No summary available</p>
      )}
    </div>
  );
}

function KeyTermsCard({
  keyTerms,
}: {
  keyTerms: Array<{ term: string; definition: string }>;
}) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Key Terms</h3>
      </div>

      {keyTerms.length > 0 ? (
        <div className="space-y-3">
          {keyTerms.slice(0, 5).map((kt, i) => (
            <div key={i} className="border-b pb-2 last:border-0">
              <p className="text-sm font-medium">{kt.term}</p>
              <p className="text-xs text-muted-foreground">{kt.definition}</p>
            </div>
          ))}
          {keyTerms.length > 5 && (
            <p className="text-xs text-muted-foreground">
              + {keyTerms.length - 5} more terms
            </p>
          )}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No key terms identified</p>
      )}
    </div>
  );
}

function RisksList({
  risks,
}: {
  risks: Array<{
    id: string;
    risk_level: string;
    category: string;
    description: string;
    recommendation: string;
  }>;
}) {
  if (risks.length === 0) {
    return null;
  }

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-semibold mb-4">Risk Details & Recommendations</h3>
      <div className="space-y-4">
        {risks.map((risk) => (
          <div key={risk.id} className="border rounded p-3">
            <div className="flex items-center gap-2 mb-2">
              <RiskBadge level={risk.risk_level} />
              <span className="font-medium">{risk.category}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              {risk.description}
            </p>
            {risk.recommendation && (
              <div className="bg-muted/50 rounded p-2">
                <p className="text-sm">
                  <span className="font-medium">Recommendation: </span>
                  {risk.recommendation}
                </p>
              </div>
            )}
          </div>
        ))}
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

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded-full ${
        styles[level] || "bg-gray-100 text-gray-800"
      }`}
    >
      {level}
    </span>
  );
}
