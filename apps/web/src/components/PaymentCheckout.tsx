import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CreditCard, Loader2, CheckCircle, XCircle } from "lucide-react";
import { paymentsApi, type CreateOrderResponse } from "../lib/payments";

interface PaymentCheckoutProps {
  selectedPlan: string | null;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function PaymentCheckout({
  selectedPlan,
  onSuccess,
  onCancel,
}: PaymentCheckoutProps) {
  const [order, setOrder] = useState<CreateOrderResponse | null>(null);

  const createOrderMutation = useMutation({
    mutationFn: paymentsApi.createOrder,
    onSuccess: (data) => {
      setOrder(data);
    },
  });

  const verifyPaymentMutation = useMutation({
    mutationFn: ({
      orderId,
      paymentId,
      signature,
    }: {
      orderId: string;
      paymentId: string;
      signature: string;
    }) => paymentsApi.verifyPayment(orderId, paymentId, signature),
    onSuccess: () => {
      onSuccess?.();
    },
  });

  const handleCreateOrder = () => {
    if (selectedPlan) {
      createOrderMutation.mutate(selectedPlan);
    }
  };

  const handlePaymentComplete = () => {
    if (order) {
      // Mock payment completion for demo
      verifyPaymentMutation.mutate({
        orderId: order.order_id,
        paymentId: "pay_mock_" + Date.now(),
        signature: "sig_mock_" + Date.now(),
      });
    }
  };

  if (createOrderMutation.isPending) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (createOrderMutation.isError) {
    return (
      <div className="text-center py-8">
        <XCircle className="h-12 w-12 mx-auto text-red-500 mb-4" />
        <p className="text-muted-foreground mb-4">Failed to create order</p>
        <button
          onClick={handleCreateOrder}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (order) {
    return (
      <div className="border rounded-lg p-6">
        <div className="text-center mb-6">
          <CreditCard className="h-12 w-12 mx-auto text-primary mb-4" />
          <h3 className="text-lg font-semibold mb-2">Complete Payment</h3>
          <p className="text-muted-foreground">
            You are subscribing to the {order.plan_name}
          </p>
        </div>

        <div className="bg-muted rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm">Plan</span>
            <span className="font-medium">{order.plan_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">Amount</span>
            <span className="font-medium">
              ₹{(order.amount / 100).toFixed(2)}
            </span>
          </div>
        </div>

        <div className="space-y-3">
          <button
            onClick={handlePaymentComplete}
            disabled={verifyPaymentMutation.isPending}
            className="w-full py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {verifyPaymentMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Processing...
              </span>
            ) : (
              "Pay Now"
            )}
          </button>

          <button
            onClick={onCancel}
            className="w-full py-2 border rounded-md hover:bg-muted"
          >
            Cancel
          </button>
        </div>

        {verifyPaymentMutation.isSuccess && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-sm text-green-800">Payment successful!</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="text-center py-8">
      <p className="text-muted-foreground mb-4">Select a plan to continue</p>
      <button
        onClick={handleCreateOrder}
        disabled={!selectedPlan}
        className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
      >
        Proceed to Payment
      </button>
    </div>
  );
}
