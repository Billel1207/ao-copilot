/**
 * Tests for SummaryTab component.
 * Verifies rendering of project_overview, key_points, risks, and actions_next_48h.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { SummaryTab } from "./SummaryTab";
import { vi } from "vitest";

// ── Mocks ─────────────────────────────────────────────────────────────────

vi.mock("@/components/ui/CitationTooltip", () => ({
  CitationTooltip: ({ citations }: { citations: unknown[] }) => (
    <span data-testid="citation-tooltip">{citations?.length ?? 0} sources</span>
  ),
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function makeSummary(overrides: Record<string, unknown> = {}) {
  return {
    project_overview: {
      title: "Construction école primaire",
      buyer: "Mairie de Lyon",
      scope: "Construction complète d'une école 12 classes",
      location: "Lyon 3e, Rhône",
      deadline_submission: "15/04/2026",
      site_visit_required: false,
      market_type: "Travaux",
      estimated_budget: "2,5 M€",
    },
    key_points: [],
    risks: [],
    actions_next_48h: [],
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("SummaryTab", () => {
  it("renders project overview cards", () => {
    const summary = makeSummary();
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Mairie de Lyon")).toBeInTheDocument();
    expect(screen.getByText("Travaux")).toBeInTheDocument();
    expect(screen.getByText("15/04/2026")).toBeInTheDocument();
    expect(screen.getByText("2,5 M€")).toBeInTheDocument();
  });

  it("renders location when provided", () => {
    const summary = makeSummary();
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Lyon 3e, Rhône")).toBeInTheDocument();
  });

  it("renders scope section", () => {
    const summary = makeSummary();
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Périmètre")).toBeInTheDocument();
    expect(screen.getByText("Construction complète d'une école 12 classes")).toBeInTheDocument();
  });

  it("shows site visit warning when required", () => {
    const summary = makeSummary({
      project_overview: {
        ...makeSummary().project_overview,
        site_visit_required: true,
      },
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText(/Visite de site obligatoire/)).toBeInTheDocument();
  });

  it("does not show site visit warning when not required", () => {
    const summary = makeSummary();
    render(<SummaryTab summary={summary as never} />);

    expect(screen.queryByText(/Visite de site obligatoire/)).not.toBeInTheDocument();
  });

  it("renders key points table", () => {
    const summary = makeSummary({
      key_points: [
        { label: "Durée marché", value: "24 mois", citations: [{ doc: "RC.pdf", page: 3, quote: "test" }] },
        { label: "Garantie", value: "10 ans", citations: [] },
      ],
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Points clés")).toBeInTheDocument();
    expect(screen.getByText("Durée marché")).toBeInTheDocument();
    expect(screen.getByText("24 mois")).toBeInTheDocument();
    expect(screen.getByText("Garantie")).toBeInTheDocument();
    expect(screen.getByText("10 ans")).toBeInTheDocument();
  });

  it("renders risk items with severity badges", () => {
    const summary = makeSummary({
      risks: [
        { risk: "Pénalités élevées", severity: "high", why: "1/1000e par jour", citations: [] },
        { risk: "Délais serrés", severity: "medium", why: "Planning ambitieux", citations: [] },
        { risk: "Clause standard", severity: "low", why: "RAS", citations: [] },
      ],
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Risques identifiés")).toBeInTheDocument();
    expect(screen.getByText("Pénalités élevées")).toBeInTheDocument();
    expect(screen.getByText("Délais serrés")).toBeInTheDocument();
    expect(screen.getByText("Clause standard")).toBeInTheDocument();
    expect(screen.getByText(/éliminatoire/)).toBeInTheDocument();
    expect(screen.getByText(/majeur/)).toBeInTheDocument();
    expect(screen.getByText(/mineur/)).toBeInTheDocument();
  });

  it("renders risk count pills", () => {
    const summary = makeSummary({
      risks: [
        { risk: "R1", severity: "high", why: "x", citations: [] },
        { risk: "R2", severity: "high", why: "x", citations: [] },
        { risk: "R3", severity: "medium", why: "x", citations: [] },
      ],
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText(/2 éliminatoires/)).toBeInTheDocument();
    expect(screen.getByText(/1 majeur/)).toBeInTheDocument();
  });

  it("renders actions_next_48h with priorities", () => {
    const summary = makeSummary({
      actions_next_48h: [
        { action: "Obtenir attestation visite", owner_role: "Chef de projet", priority: "P0" },
        { action: "Préparer mémoire technique", owner_role: "Ingénieur", priority: "P1" },
      ],
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Actions à prendre sous 48h")).toBeInTheDocument();
    expect(screen.getByText("Obtenir attestation visite")).toBeInTheDocument();
    expect(screen.getByText("Chef de projet")).toBeInTheDocument();
    expect(screen.getByText("P0")).toBeInTheDocument();
    expect(screen.getByText("Préparer mémoire technique")).toBeInTheDocument();
    expect(screen.getByText("P1")).toBeInTheDocument();
  });

  it("does not render sections when arrays are empty", () => {
    const summary = makeSummary({ key_points: [], risks: [], actions_next_48h: [] });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.queryByText("Points clés")).not.toBeInTheDocument();
    expect(screen.queryByText("Risques identifiés")).not.toBeInTheDocument();
    expect(screen.queryByText("Actions à prendre sous 48h")).not.toBeInTheDocument();
  });

  it("shows 'Non précisé' when estimated_budget is null", () => {
    const summary = makeSummary({
      project_overview: {
        ...makeSummary().project_overview,
        estimated_budget: null,
      },
    });
    render(<SummaryTab summary={summary as never} />);

    expect(screen.getByText("Non précisé")).toBeInTheDocument();
  });
});
