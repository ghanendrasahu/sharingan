import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Cancel, Loader2, Calendar, CreditCard } from "lucide-react";
import { paymentsApi } from "../lib/payments";

interface SubscriptionStatusProps {
  onCancel?: () => void;
}

export function SubscriptionStatus({ onCancel }: SubscriptionStatusProps) {
  const queryClient = useQueryClient();
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const { data: subscription, isLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: () => paymentsApi.getSubscription(),
  });

  const cancelMutation = useMutation({
    mutationFn: (subscriptionId: string) =>
      paymentsApi.cancelSubscription({ subscription_id: subscriptionId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
      setShowCancelConfirm(false);
      onCancel?.();
    },
  });

  if (isLoading) {
    return (
      <div className="border rounded-lg p-6 animate-pulse">
        <div className="h-4 bg-muted rounded w-32 mb-4" />
        <div className="h-8 bg-muted rounded w-48" />
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="border rounded-lg p-6">
        <p className="text-muted-foreground">No active subscription</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Subscription Details</h3>
          <span
            className={`text-xs px-2 py-1 rounded ${
              subscription.status === "active"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {subscription.status === "active" ? "Active" : "Cancelled"}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Plan</p>
            <p className="font-medium capitalize">{subscription.plan_type}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Credits</p>
            <p className="font-medium">
              {subscription.credits_remaining}
              <span className="text-muted-foreground">
                /{subscription.credits_used + subscription.credits_remaining}
              </span>
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Started</p>
            <p className="font-medium flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {subscription.started_at
                ? new Date(subscription.started_at).toLocaleDateString()
                : "N/A"}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Payment</p>
            <p className="font-medium flex items-center gap-1">
              <CreditCard className="h-3 w-3" />
              {subscription.plan_type === "free" ? "N/A" : "Razorpay"}
            </p>
          </div>
        </div>
      </div>

      {subscription.plan_type !== "free" && (
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium">Cancel Subscription</h4>
              <p className="text-sm text-muted-foreground">
                Your subscription will remain active until the end of the
                billing period.
              </p>
            </div>
            <button
              onClick={() => setShowCancelConfirm(true)}
              className="px-4 py-2 border border-red-500 text-red-500 rounded-md hover:bg-red-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {showCancelConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-2 mb-4">
              <Cancel className="h-5 w-5 text-red-500" />
              <h3 className="text-lg font-medium">Cancel Subscription</h3>
            </div>

            <p className="text-muted-foreground mb-6">
              Are you sure you want to cancel your subscription? You will lose
              access to premium features at the end of your billing period.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowCancelConfirm(false)}
                className="flex-1 py-2 px-4 border rounded-md hover:bg-muted transition-colors"
              >
                Keep Subscription
              </button>
              <button
                onClick={() => {
                  if (subscription.subscription_id) {
                    cancelMutation.mutate(subscription.subscription_id);
                  }
                }}
                disabled={cancelMutation.isPending}
                className="flex-1 py-2 px-4 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
              >
                {cancelMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Confirm Cancellation"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
