import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CreditCard, Settings } from "lucide-react";
import { PlanSelector } from "../components/PlanSelector";
import { SubscriptionManager } from "../components/SubscriptionManager";
import { PaymentCheckout } from "../components/PaymentCheckout";

const queryClient = new QueryClient();

export function PaymentPage() {
  const [activeTab, setActiveTab] = useState<"plans" | "subscription">("plans");
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [showCheckout, setShowCheckout] = useState(false);

  const handleSelectPlan = (planType: string) => {
    setSelectedPlan(planType);
    setShowCheckout(true);
  };

  const handleCheckoutSuccess = () => {
    setShowCheckout(false);
    setSelectedPlan(null);
    queryClient.invalidateQueries({ queryKey: ["subscription"] });
    setActiveTab("subscription");
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Subscription & Billing</h1>
          <p className="text-muted-foreground mt-2">
            Manage your subscription and billing preferences.
          </p>
        </div>

        <div className="flex gap-4 mb-6">
          <TabButton
            active={activeTab === "plans"}
            onClick={() => setActiveTab("plans")}
            icon={<CreditCard className="h-4 w-4" />}
            label="Plans"
          />
          <TabButton
            active={activeTab === "subscription"}
            onClick={() => setActiveTab("subscription")}
            icon={<Settings className="h-4 w-4" />}
            label="My Subscription"
          />
        </div>

        {activeTab === "plans" ? (
          <div className="space-y-6">
            {showCheckout && selectedPlan ? (
              <PaymentCheckout
                selectedPlan={selectedPlan}
                onSuccess={handleCheckoutSuccess}
                onCancel={() => {
                  setShowCheckout(false);
                  setSelectedPlan(null);
                }}
              />
            ) : (
              <PlanSelector
                selectedPlan={selectedPlan}
                onSelectPlan={handleSelectPlan}
              />
            )}
          </div>
        ) : (
          <SubscriptionManager />
        )}
      </div>
    </QueryClientProvider>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
        active
          ? "bg-primary text-primary-foreground"
          : "bg-muted hover:bg-muted/80"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
