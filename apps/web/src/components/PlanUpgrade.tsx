import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowUp,
  ArrowDown,
  Check,
  X,
  CreditCard,
  Loader2,
} from "lucide-react";
import { paymentsApi, type Plan } from "../lib/payments";

interface PlanUpgradeProps {
  currentPlan: string;
  onSuccess?: () => void;
}

export function PlanUpgrade({ currentPlan, onSuccess }: PlanUpgradeProps) {
  const queryClient = useQueryClient();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const { data: plans } = useQuery({
    queryKey: ["plans"],
    queryFn: () => paymentsApi.getPlans(),
  });

  const createOrderMutation = useMutation({
    mutationFn: (planType: string) =>
      paymentsApi.createOrder({ plan_type: planType as Plan }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      queryClient.invalidateQueries({ queryKey: ["subscription"] });
      onSuccess?.();
    },
  });

  const handlePlanSelect = (planType: string) => {
    if (planType === currentPlan) return;
    setSelectedPlan(planType);
    setShowConfirm(true);
  };

  const handleConfirmUpgrade = () => {
    if (selectedPlan) {
      createOrderMutation.mutate(selectedPlan);
    }
  };

  const currentPlanDetails = plans?.find((p) => p.plan_type === currentPlan);

  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">Current Plan</h3>
            <p className="text-sm text-muted-foreground">
              {currentPlanDetails?.name || "Free Plan"}
            </p>
          </div>
          <div className="text-right">
            <p className="font-medium">
              ₹{currentPlanDetails?.price_inr || 0}/month
            </p>
            <p className="text-sm text-muted-foreground">
              {currentPlanDetails?.credits_per_month || 5} credits
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plans?.map((plan) => {
          const isCurrent = plan.plan_type === currentPlan;
          const isUpgrade =
            plans.findIndex((p) => p.plan_type === plan.plan_type) >
            plans.findIndex((p) => p.plan_type === currentPlan);
          const isDowngrade =
            plans.findIndex((p) => p.plan_type === plan.plan_type) <
            plans.findIndex((p) => p.plan_type === currentPlan);

          return (
            <div
              key={plan.plan_type}
              className={`border rounded-lg p-4 cursor-pointer transition-all ${
                isCurrent
                  ? "border-primary bg-primary/5"
                  : "hover:border-primary/50"
              } ${selectedPlan === plan.plan_type ? "border-primary" : ""}`}
              onClick={() => !isCurrent && handlePlanSelect(plan.plan_type)}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{plan.name}</h3>
                {isCurrent && (
                  <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                    Current
                  </span>
                )}
                {!isCurrent && isUpgrade && (
                  <ArrowUp className="h-4 w-4 text-green-500" />
                )}
                {!isCurrent && isDowngrade && (
                  <ArrowDown className="h-4 w-4 text-orange-500" />
                )}
              </div>
              <p className="text-2xl font-bold mb-2">
                ₹{plan.price_inr}
                <span className="text-sm font-normal text-muted-foreground">
                  /month
                </span>
              </p>
              <ul className="space-y-1">
                {plan.features.slice(0, 3).map((feature, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-2 text-sm text-muted-foreground"
                  >
                    <Check className="h-3 w-3 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
              {!isCurrent && (
                <button
                  className="mt-4 w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                  disabled={isCurrent}
                >
                  {isUpgrade ? "Upgrade" : "Downgrade"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {showConfirm && selectedPlan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Confirm Plan Change</h3>
              <button onClick={() => setShowConfirm(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">From</p>
                <p className="font-medium">
                  {currentPlanDetails?.name || "Free Plan"}
                </p>
              </div>

              <div className="border rounded-lg p-4">
                <p className="text-sm text-muted-foreground">To</p>
                <p className="font-medium">
                  {plans?.find((p) => p.plan_type === selectedPlan)?.name}
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 py-2 px-4 border rounded-md hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmUpgrade}
                  disabled={createOrderMutation.isPending}
                  className="flex-1 py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
                >
                  {createOrderMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CreditCard className="h-4 w-4" />
                  )}
                  Confirm Change
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
