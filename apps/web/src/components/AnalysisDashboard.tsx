import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Play,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { analysisApi, type AnalysisResult } from "../lib/analysis";
import { RiskVisualization } from "./RiskVisualization";
import { AnalysisResults } from "./AnalysisResults";

interface AnalysisDashboardProps {
  documentId: string;
}

export function AnalysisDashboard({ documentId }: AnalysisDashboardProps) {
  const queryClient = useQueryClient();
  const [selectedAnalysis, setSelectedAnalysis] =
    useState<AnalysisResult | null>(null);

  const { data: analysesData, isLoading } = useQuery({
    queryKey: ["analyses", documentId],
    queryFn: () => analysisApi.listAnalyses(documentId),
  });

  const startAnalysisMutation = useMutation({
    mutationFn: analysisApi.startAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analyses", documentId] });
    },
  });

  const analyses = analysesData?.analyses || [];

  const handleStartAnalysis = () => {
    startAnalysisMutation.mutate({ document_id: documentId });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading analyses...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Document Analysis</h2>
        <button
          onClick={handleStartAnalysis}
          disabled={startAnalysisMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          <Play className="h-4 w-4" />
          {startAnalysisMutation.isPending
            ? "Starting..."
            : "Run New Analysis"}
        </button>
      </div>

      {analyses.length === 0 ? (
        <div className="border rounded-lg p-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Analyses Yet</h3>
          <p className="text-muted-foreground mb-4">
            Run your first analysis to get insights about this document.
          </p>
          <button
            onClick={handleStartAnalysis}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Start Analysis
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 border rounded-lg p-4">
            <h3 className="font-semibold mb-4">Analysis History</h3>
            <div className="space-y-2">
              {analyses.map((analysis) => (
                <AnalysisListItem
                  key={analysis.analysis_id}
                  analysis={analysis}
                  isSelected={
                    selectedAnalysis?.analysis_id === analysis.analysis_id
                  }
                  onClick={() => setSelectedAnalysis(analysis)}
                />
              ))}
            </div>
          </div>

          <div className="lg:col-span-2">
            {selectedAnalysis ? (
              <AnalysisDetail analysis={selectedAnalysis} />
            ) : (
              <div className="flex items-center justify-center h-64 border rounded-lg">
                <p className="text-muted-foreground">
                  Select an analysis to view results
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AnalysisListItem({
  analysis,
  isSelected,
  onClick,
}: {
  analysis: AnalysisResult;
  isSelected: boolean;
  onClick: () => void;
}) {
  const getStatusIcon = () => {
    switch (analysis.status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "processing":
        return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div
      className={`p-3 border rounded cursor-pointer hover:bg-muted/50 transition-colors ${
        isSelected ? "border-primary bg-primary/5" : ""
      }`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 mb-1">
        {getStatusIcon()}
        <span className="text-sm font-medium capitalize">
          {analysis.status}
        </span>
      </div>
      <p className="text-xs text-muted-foreground">
        {new Date(analysis.created_at).toLocaleString()}
      </p>
      {analysis.status === "completed" && (
        <div className="flex items-center gap-2 mt-2">
          <RiskBadge level={analysis.risk_level} />
          <span className="text-xs text-muted-foreground">
            Score: {Math.round(analysis.overall_risk_score * 100)}
          </span>
        </div>
      )}
    </div>
  );
}

function AnalysisDetail({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="space-y-6">
      {analysis.status === "completed" ? (
        <>
          <RiskVisualization
            overallRiskScore={analysis.overall_risk_score}
            riskLevel={analysis.risk_level}
            risks={analysis.risks}
          />
          <AnalysisResults result={analysis} />
        </>
      ) : analysis.status === "processing" ? (
        <div className="flex flex-col items-center justify-center h-64 border rounded-lg">
          <RefreshCw className="h-12 w-12 text-primary animate-spin mb-4" />
          <h3 className="text-lg font-semibold mb-2">Processing Analysis</h3>
          <p className="text-muted-foreground">
            This analysis is currently being processed. Please wait...
          </p>
        </div>
      ) : analysis.status === "failed" ? (
        <div className="flex flex-col items-center justify-center h-64 border rounded-lg">
          <XCircle className="h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Analysis Failed</h3>
          <p className="text-muted-foreground">
            This analysis failed to complete. Please try again.
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 border rounded-lg">
          <Clock className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">Analysis Pending</h3>
          <p className="text-muted-foreground">
            This analysis is waiting to be processed.
          </p>
        </div>
      )}
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
