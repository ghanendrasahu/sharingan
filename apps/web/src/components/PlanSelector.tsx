import { useQuery } from "@tanstack/react-query";
import { Check, Star, Zap, Building2 } from "lucide-react";
import { paymentsApi, type Plan } from "../lib/payments";

interface PlanSelectorProps {
  selectedPlan: string | null;
  onSelectPlan: (planType: string) => void;
}

export function PlanSelector({ selectedPlan, onSelectPlan }: PlanSelectorProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["plans"],
    queryFn: () => paymentsApi.getPlans(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading plans...</div>
      </div>
    );
  }

  const plans = data?.plans || [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {plans.map((plan) => (
        <PlanCard
          key={plan.plan_id}
          plan={plan}
          isSelected={selectedPlan === plan.plan_type}
          onSelect={() => onSelectPlan(plan.plan_type)}
        />
      ))}
    </div>
  );
}

function PlanCard({
  plan,
  isSelected,
  onSelect,
}: {
  plan: Plan;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const getIcon = () => {
    switch (plan.plan_type) {
      case "starter":
        return <Zap className="h-6 w-6" />;
      case "professional":
        return <Star className="h-6 w-6" />;
      case "enterprise":
        return <Building2 className="h-6 w-6" />;
      default:
        return <Check className="h-6 w-6" />;
    }
  };

  const isPopular = plan.plan_type === "professional";

  return (
    <div
      className={`border rounded-lg p-6 cursor-pointer transition-all ${
        isSelected
          ? "border-primary ring-2 ring-primary/20"
          : "hover:border-primary/50"
      } ${isPopular ? "relative" : ""}`}
      onClick={onSelect}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="bg-primary text-primary-foreground px-3 py-1 text-xs font-medium rounded-full">
            Most Popular
          </span>
        </div>
      )}

      <div className="text-center mb-4">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary mb-4">
          {getIcon()}
        </div>
        <h3 className="text-lg font-semibold">{plan.name}</h3>
        <div className="mt-2">
          <span className="text-3xl font-bold">₹{plan.price_inr}</span>
          <span className="text-muted-foreground">/month</span>
        </div>
      </div>

      <ul className="space-y-3 mb-6">
        <li className="flex items-center gap-2">
          <Check className="h-4 w-4 text-green-500" />
          <span className="text-sm">{plan.credits_per_month} analyses/month</span>
        </li>
        <li className="flex items-center gap-2">
          <Check className="h-4 w-4 text-green-500" />
          <span className="text-sm">
            {plan.max_documents === -1 ? "Unlimited" : plan.max_documents} documents
          </span>
        </li>
        <li className="flex items-center gap-2">
          <Check className="h-4 w-4 text-green-500" />
          <span className="text-sm">Up to {plan.max_upload_size_mb}MB uploads</span>
        </li>
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-500" />
            <span className="text-sm">{feature}</span>
          </li>
        ))}
      </ul>

      <button
        className={`w-full py-2 rounded-md transition-colors ${
          isSelected
            ? "bg-primary text-primary-foreground"
            : "bg-muted hover:bg-muted/80"
        }`}
      >
        {isSelected ? "Selected" : "Select Plan"}
      </button>
    </div>
  );
}
