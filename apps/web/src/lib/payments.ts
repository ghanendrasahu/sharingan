import api from "./api";

export interface Plan {
  plan_id: string;
  name: string;
  plan_type: string;
  price_inr: number;
  credits_per_month: number;
  max_documents: number;
  max_upload_size_mb: number;
  features: string[];
}

export interface Subscription {
  subscription_id: string;
  plan_type: string;
  status: string;
  credits_remaining: number;
  credits_used: number;
  started_at: string;
  expires_at: string | null;
}

export interface CreateOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  plan_id: string;
  plan_name: string;
  razorpay_key_id: string;
}

export const paymentsApi = {
  async getPlans(): Promise<{ plans: Plan[] }> {
    const response = await api.get("/payments/plans");
    return response.data;
  },

  async createOrder(planType: string): Promise<CreateOrderResponse> {
    const response = await api.post("/payments/create-order", {
      plan_type: planType,
    });
    return response.data;
  },

  async verifyPayment(
    orderId: string,
    paymentId: string,
    signature: string
  ): Promise<{ verified: boolean; subscription_id: string | null }> {
    const response = await api.post("/payments/verify", {
      razorpay_order_id: orderId,
      razorpay_payment_id: paymentId,
      razorpay_signature: signature,
    });
    return response.data;
  },

  async getSubscription(): Promise<Subscription> {
    const response = await api.get("/payments/subscription");
    return response.data;
  },

  async cancelSubscription(
    subscriptionId: string
  ): Promise<{ cancelled: boolean }> {
    const response = await api.post("/payments/cancel", {
      subscription_id: subscriptionId,
    });
    return response.data;
  },
};
