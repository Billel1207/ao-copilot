/**
 * Tests for PlanCards component.
 * Verifies plan display, feature lists, CTA buttons, badges, and loading states.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import PlanCards from "./PlanCards";
import { PlanInfo } from "@/stores/billing";

// ── Helpers ───────────────────────────────────────────────────────────────

function makePlan(overrides: Partial<PlanInfo> & { id: string; name: string }): PlanInfo {
  return {
    monthly_eur: 0,
    docs_per_month: 5,
    max_users: 1,
    word_export: false,
    features: ["Feature A", "Feature B", "Feature C", "Feature D"],
    ...overrides,
  };
}

const FREE_PLAN = makePlan({ id: "free", name: "Free", monthly_eur: 0, docs_per_month: 5, max_users: 1 });
const STARTER_PLAN = makePlan({ id: "starter", name: "Starter", monthly_eur: 69, docs_per_month: 15, max_users: 1, stripe_price_id: "price_starter" });
const PRO_PLAN = makePlan({ id: "pro", name: "Pro", monthly_eur: 179, docs_per_month: 60, max_users: 5, word_export: true, stripe_price_id: "price_pro" });
const BUSINESS_PLAN = makePlan({ id: "business", name: "Business", monthly_eur: 499, docs_per_month: 999, max_users: 999 });
const EUROPE_PLAN = makePlan({ id: "europe", name: "Europe", monthly_eur: 299, docs_per_month: 100, max_users: 20 });

const ALL_PLANS = [FREE_PLAN, STARTER_PLAN, PRO_PLAN, BUSINESS_PLAN, EUROPE_PLAN];

// ── Tests ─────────────────────────────────────────────────────────────────

describe("PlanCards", () => {
  const onUpgrade = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all plan names and prices", () => {
    render(<PlanCards plans={ALL_PLANS} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByText("Starter")).toBeInTheDocument();
    expect(screen.getByText("Pro")).toBeInTheDocument();
    expect(screen.getByText("Business")).toBeInTheDocument();
    expect(screen.getByText("Europe")).toBeInTheDocument();

    expect(screen.getByText("Gratuit")).toBeInTheDocument();
    expect(screen.getByText("69€")).toBeInTheDocument();
    expect(screen.getByText("179€")).toBeInTheDocument();
  });

  it("shows 'Actuel' badge on the current plan", () => {
    render(<PlanCards plans={[FREE_PLAN, STARTER_PLAN]} currentPlan="starter" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Actuel")).toBeInTheDocument();
    // The current plan button says "Plan actuel"
    expect(screen.getByText("Plan actuel")).toBeInTheDocument();
  });

  it("shows 'Recommandé' badge on Pro plan", () => {
    render(<PlanCards plans={[STARTER_PLAN, PRO_PLAN]} currentPlan="starter" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Recommandé")).toBeInTheDocument();
  });

  it("shows 'Enterprise' badge on Business plan", () => {
    render(<PlanCards plans={[STARTER_PLAN, BUSINESS_PLAN]} currentPlan="starter" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Enterprise")).toBeInTheDocument();
  });

  it("shows 'Export Word inclus' for plans with word_export", () => {
    render(<PlanCards plans={[PRO_PLAN]} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Export Word inclus")).toBeInTheDocument();
  });

  it("does not show 'Export Word inclus' for plans without word_export", () => {
    render(<PlanCards plans={[STARTER_PLAN]} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.queryByText("Export Word inclus")).not.toBeInTheDocument();
  });

  it("shows 'Illimité' for 999 docs_per_month", () => {
    render(<PlanCards plans={[BUSINESS_PLAN]} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.getAllByText(/Illimité/).length).toBeGreaterThanOrEqual(1);
  });

  it("calls onUpgrade when clicking an upgrade button", () => {
    render(
      <PlanCards
        plans={[FREE_PLAN, STARTER_PLAN]}
        currentPlan="free"
        onUpgrade={onUpgrade}
      />
    );

    const upgradeBtn = screen.getByText("Passer au Starter");
    fireEvent.click(upgradeBtn);

    expect(onUpgrade).toHaveBeenCalledWith("starter");
  });

  it("disables current plan button", () => {
    render(<PlanCards plans={[STARTER_PLAN]} currentPlan="starter" onUpgrade={onUpgrade} />);

    const btn = screen.getByText("Plan actuel");
    expect(btn).toBeDisabled();
  });

  it("shows payment methods for paid plans only", () => {
    render(<PlanCards plans={[FREE_PLAN, STARTER_PLAN]} currentPlan="free" onUpgrade={onUpgrade} />);

    // "Paiement sécurisé via Stripe" should appear once (for Starter, not Free)
    const stripeTexts = screen.getAllByText("Paiement sécurisé via Stripe");
    expect(stripeTexts).toHaveLength(1);
  });

  it("shows 'Demander un devis' for Business without stripe_price_id", () => {
    render(<PlanCards plans={[BUSINESS_PLAN]} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Demander un devis")).toBeInTheDocument();
  });

  it("renders feature list items (skipping first 2)", () => {
    const plan = makePlan({
      id: "starter",
      name: "Starter",
      monthly_eur: 69,
      features: ["feat1", "feat2", "Custom feature 3", "Custom feature 4"],
      stripe_price_id: "price_x",
    });
    render(<PlanCards plans={[plan]} currentPlan="free" onUpgrade={onUpgrade} />);

    expect(screen.getByText("Custom feature 3")).toBeInTheDocument();
    expect(screen.getByText("Custom feature 4")).toBeInTheDocument();
    // First two features should NOT be in the features list area
    expect(screen.queryByText("feat1")).not.toBeInTheDocument();
    expect(screen.queryByText("feat2")).not.toBeInTheDocument();
  });
});
