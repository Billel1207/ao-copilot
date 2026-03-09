import { create } from "zustand";
import { billingApi } from "@/lib/api";

export interface PlanInfo {
  id: string;
  name: string;
  monthly_eur: number;
  docs_per_month: number;
  max_users: number;
  word_export: boolean;
  features: string[];
}

export interface BillingUsage {
  org_id: string;
  plan: string;
  plan_name: string;
  docs_used_this_month: number;
  docs_quota: number;
  quota_pct: number;
  period_year: number;
  period_month: number;
  word_export_allowed: boolean;
  plans_available: PlanInfo[];
}

export interface BillingSubscription {
  org_id: string;
  plan: string;
  status: string;
  stripe_subscription_id: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

interface BillingState {
  usage: BillingUsage | null;
  subscription: BillingSubscription | null;
  isLoading: boolean;
  /** Plan en cours de checkout (null = aucun) — évite que les deux boutons se grisent */
  checkoutPlan: "starter" | "pro" | null;
  error: string | null;

  fetchBilling: () => Promise<void>;
  createCheckout: (plan: "starter" | "pro") => Promise<void>;
  openPortal: () => Promise<void>;
}

export const useBillingStore = create<BillingState>((set) => ({
  usage: null,
  subscription: null,
  isLoading: false,
  checkoutPlan: null,
  error: null,

  fetchBilling: async () => {
    set({ isLoading: true, error: null });
    try {
      const [usageRes, subRes] = await Promise.all([
        billingApi.getUsage(),
        billingApi.getSubscription(),
      ]);
      set({
        usage: usageRes.data,
        subscription: subRes.data,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const msg =
        axiosErr?.response?.data?.detail ||
        (err instanceof Error ? err.message : "Erreur chargement billing");
      set({ error: msg, isLoading: false });
    }
  },

  createCheckout: async (plan) => {
    set({ checkoutPlan: plan, error: null });
    try {
      const origin = window.location.origin;
      const res = await billingApi.createCheckout(
        plan,
        `${origin}/billing?success=true`,
        `${origin}/billing?canceled=true`
      );
      // Rediriger vers Stripe Checkout
      window.location.href = res.data.checkout_url;
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
      const status = axiosErr?.response?.status;
      const detail = axiosErr?.response?.data?.detail;
      const msg =
        status === 503
          ? "Service de paiement temporairement indisponible. Veuillez réessayer dans quelques instants ou contacter le support."
          : detail || (err instanceof Error ? err.message : "Erreur création checkout");
      set({ error: msg, checkoutPlan: null });
    }
  },

  openPortal: async () => {
    set({ isLoading: true, error: null });
    try {
      const origin = window.location.origin;
      const res = await billingApi.createPortal(`${origin}/billing`);
      window.location.href = res.data.portal_url;
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
      const status = axiosErr?.response?.status;
      const detail = axiosErr?.response?.data?.detail;
      const msg =
        status === 503
          ? "Service de paiement temporairement indisponible. Veuillez réessayer dans quelques instants."
          : detail || (err instanceof Error ? err.message : "Erreur portail billing");
      set({ error: msg, isLoading: false });
    }
  },
}));
