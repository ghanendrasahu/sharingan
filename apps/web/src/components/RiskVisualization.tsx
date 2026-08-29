import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { cn } from "../lib/utils";

interface RiskVisualizationProps {
  overallRiskScore: number;
  riskLevel: "high" | "medium" | "low";
  risks: Array<{
    id: string;
    risk_level: "high" | "medium" | "low";
    category: string;
    description: string;
  }>;
}

export function RiskVisualization({
  overallRiskScore,
  riskLevel,
  risks,
}: RiskVisualizationProps) {
  const highRisks = risks.filter((r) => r.risk_level === "high");
  const mediumRisks = risks.filter((r) => r.risk_level === "medium");
  const lowRisks = risks.filter((r) => r.risk_level === "low");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <RiskGauge score={overallRiskScore} level={riskLevel} />
        <div className="flex-1">
          <h3 className="text-lg font-semibold">Overall Risk Assessment</h3>
          <p className="text-muted-foreground">
            {riskLevel === "high" && "This document contains significant risks that require immediate attention."}
            {riskLevel === "medium" && "This document has moderate risks that should be reviewed."}
            {riskLevel === "low" && "This document has minimal risks identified."}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <RiskCard
          count={highRisks.length}
          label="High Risk"
          icon={<XCircle className="h-5 w-5 text-red-500" />}
        />
        <RiskCard
          count={mediumRisks.length}
          label="Medium Risk"
          icon={<AlertTriangle className="h-5 w-5 text-yellow-500" />}
        />
        <RiskCard
          count={lowRisks.length}
          label="Low Risk"
          icon={<CheckCircle className="h-5 w-5 text-green-500" />}
        />
      </div>

      {risks.length > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-3">Risk Breakdown</h4>
          <div className="space-y-2">
            {risks.map((risk) => (
              <div
                key={risk.id}
                className="flex items-start gap-3 p-2 border rounded"
              >
                <RiskBadge level={risk.risk_level} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{risk.category}</p>
                  <p className="text-sm text-muted-foreground">
                    {risk.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RiskGauge({
  score,
  level,
}: {
  score: number;
  level: string;
}) {
  const getColor = () => {
    if (level === "high") return "text-red-500";
    if (level === "medium") return "text-yellow-500";
    return "text-green-500";
  };

  const getBgColor = () => {
    if (level === "high") return "bg-red-100";
    if (level === "medium") return "bg-yellow-100";
    return "bg-green-100";
  };

  return (
    <div
      className={cn(
        "w-24 h-24 rounded-full flex items-center justify-center",
        getBgColor()
      )}
    >
      <div className="text-center">
        <span className={cn("text-2xl font-bold", getColor())}>
          {Math.round(score * 100)}
        </span>
        <span className="text-xs text-muted-foreground block">/100</span>
      </div>
    </div>
  );
}

function RiskCard({
  count,
  label,
  icon,
}: {
  count: number;
  label: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>
      <p className="text-2xl font-bold">{count}</p>
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
      className={cn(
        "px-2 py-1 text-xs font-medium rounded-full",
        styles[level] || "bg-gray-100 text-gray-800"
      )}
    >
      {level}
    </span>
  );
}
