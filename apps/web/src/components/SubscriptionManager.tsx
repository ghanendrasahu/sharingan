import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CreditCard,
  Calendar,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { paymentsApi } from "../lib/payments";

export function SubscriptionManager() {
  const queryClient = useQueryClient();

  const { data: subscription, isLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: () => paymentsApi.getSubscription(),
  });

  const cancelMutation = useMutation({
    mutationFn: paymentsApi.cancelSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="text-center py-8 border rounded-lg">
        <p className="text-muted-foreground">No subscription found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Current Subscription</h3>
          <StatusBadge status={subscription.status} />
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Plan</p>
              <p className="font-medium capitalize">{subscription.plan_type}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Started</p>
              <p className="font-medium">
                {new Date(subscription.started_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Credits Used</span>
            <span className="text-sm font-medium">
              {subscription.credits_used} / {subscription.credits_remaining + subscription.credits_used}
            </span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{
                width: `${
                  (subscription.credits_used /
                    (subscription.credits_remaining + subscription.credits_used)) *
                  100
                }%`,
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {subscription.credits_remaining} credits remaining
          </p>
        </div>

        {subscription.status === "active" && subscription.plan_type !== "free" && (
          <button
            onClick={() => {
              if (confirm("Are you sure you want to cancel your subscription?")) {
                cancelMutation.mutate(subscription.subscription_id);
              }
            }}
            disabled={cancelMutation.isPending}
            className="px-4 py-2 border border-red-500 text-red-500 rounded-md hover:bg-red-50 disabled:opacity-50"
          >
            {cancelMutation.isPending ? "Cancelling..." : "Cancel Subscription"}
          </button>
        )}
      </div>

      {subscription.credits_remaining === 0 && (
        <div className="border border-yellow-500 rounded-lg p-4 bg-yellow-50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <p className="text-sm text-yellow-800">
              You have no credits remaining. Upgrade your plan to continue analyzing documents.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800",
    past_due: "bg-yellow-100 text-yellow-800",
    trial: "bg-blue-100 text-blue-800",
    expired: "bg-gray-100 text-gray-800",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded-full ${
        styles[status] || "bg-gray-100 text-gray-800"
      }`}
    >
      {status}
    </span>
  );
}
