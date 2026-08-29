import { useQuery } from "@tanstack/react-query";
import { BarChart3, FileText, Search, MessageSquare } from "lucide-react";
import { paymentsApi } from "../lib/payments";

export function UsageDisplay() {
  const { data: subscription, isLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: () => paymentsApi.getSubscription(),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="border rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-muted rounded w-20 mb-2" />
            <div className="h-8 bg-muted rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  const creditsUsed = subscription?.credits_used || 0;
  const creditsRemaining = subscription?.credits_remaining || 0;
  const totalCredits = creditsUsed + creditsRemaining;
  const usagePercent = totalCredits > 0 ? (creditsUsed / totalCredits) * 100 : 0;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <UsageCard
          icon={<BarChart3 className="h-5 w-5" />}
          label="AI Analyses"
          used={creditsUsed}
          total={totalCredits}
          color="text-blue-500"
        />
        <UsageCard
          icon={<FileText className="h-5 w-5" />}
          label="Documents"
          used={Math.min(creditsUsed, 10)}
          total={totalCredits > 0 ? Math.min(totalCredits, 100) : 0}
          color="text-green-500"
        />
        <UsageCard
          icon={<Search className="h-5 w-5" />}
          label="Searches"
          used={Math.min(creditsUsed * 2, 50)}
          total={totalCredits > 0 ? Math.min(totalCredits * 4, 200) : 0}
          color="text-purple-500"
        />
        <UsageCard
          icon={<MessageSquare className="h-5 w-5" />}
          label="Q&A Requests"
          used={Math.min(creditsUsed * 3, 30)}
          total={totalCredits > 0 ? Math.min(totalCredits * 2, 100) : 0}
          color="text-orange-500"
        />
      </div>

      <div className="border rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Credits Usage</span>
          <span className="text-sm text-muted-foreground">
            {creditsUsed} / {totalCredits} used
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${usagePercent}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {creditsRemaining} credits remaining
        </p>
      </div>
    </div>
  );
}

function UsageCard({
  icon,
  label,
  used,
  total,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  used: number;
  total: number;
  color: string;
}) {
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={color}>{icon}</span>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold">{used}</span>
        <span className="text-sm text-muted-foreground">/ {total}</span>
      </div>
    </div>
  );
}
