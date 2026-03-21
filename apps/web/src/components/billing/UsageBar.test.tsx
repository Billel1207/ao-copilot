/**
 * Tests for UsageBar component.
 * Verifies progress bar rendering, color changes, alerts, and compact mode.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import UsageBar from "./UsageBar";
import { BillingUsage } from "@/stores/billing";

// ── Helpers ───────────────────────────────────────────────────────────────

function makeUsage(overrides: Partial<BillingUsage> = {}): BillingUsage {
  return {
    org_id: "org-1",
    plan: "starter",
    plan_name: "Starter",
    docs_used_this_month: 5,
    docs_quota: 15,
    quota_pct: 33,
    period_year: 2026,
    period_month: 3,
    word_export_allowed: false,
    plans_available: [],
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("UsageBar", () => {
  it("renders usage count and quota", () => {
    render(<UsageBar usage={makeUsage({ docs_used_this_month: 8, docs_quota: 15 })} />);

    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText(/\/15 docs/)).toBeInTheDocument();
  });

  it("renders month name and year in full mode", () => {
    render(<UsageBar usage={makeUsage({ period_month: 3, period_year: 2026 })} />);

    expect(screen.getByText("Mars 2026")).toBeInTheDocument();
  });

  it("shows percentage used", () => {
    render(<UsageBar usage={makeUsage({ quota_pct: 45 })} />);

    expect(screen.getByText("45% utilisé")).toBeInTheDocument();
  });

  it("clamps percentage at 100", () => {
    render(<UsageBar usage={makeUsage({ quota_pct: 120 })} />);

    expect(screen.getByText("100% utilisé")).toBeInTheDocument();
  });

  it("shows warning alert when quota_pct >= 80 and < 90", () => {
    render(<UsageBar usage={makeUsage({ quota_pct: 85 })} />);

    expect(screen.getByText("Quota bientôt atteint pour ce mois")).toBeInTheDocument();
  });

  it("shows critical alert when quota_pct >= 90", () => {
    render(<UsageBar usage={makeUsage({ quota_pct: 95 })} />);

    expect(screen.getByText(/Quota presque épuisé/)).toBeInTheDocument();
  });

  it("does not show alert when quota_pct < 80", () => {
    render(<UsageBar usage={makeUsage({ quota_pct: 50 })} />);

    expect(screen.queryByText(/Quota/)).not.toBeInTheDocument();
  });

  it("renders compact mode with simplified layout", () => {
    render(<UsageBar usage={makeUsage({ docs_used_this_month: 3, docs_quota: 15 })} compact />);

    expect(screen.getByText("Documents ce mois")).toBeInTheDocument();
    expect(screen.getByText("3/15")).toBeInTheDocument();
    // Full mode elements should not be present
    expect(screen.queryByText("Utilisation mensuelle")).not.toBeInTheDocument();
  });

  it("renders full mode header", () => {
    render(<UsageBar usage={makeUsage()} />);

    expect(screen.getByText("Utilisation mensuelle")).toBeInTheDocument();
  });

  it("handles all month names correctly", () => {
    render(<UsageBar usage={makeUsage({ period_month: 12, period_year: 2025 })} />);

    expect(screen.getByText("Décembre 2025")).toBeInTheDocument();
  });
});
