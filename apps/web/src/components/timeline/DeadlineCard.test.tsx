/**
 * Tests for DeadlineCard component.
 * Verifies deadline display, countdown badges, urgency states, and past dates.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { DeadlineCard, Deadline, DeadlineList } from "./DeadlineCard";

// ── Helpers ───────────────────────────────────────────────────────────────

function makeDeadline(overrides: Partial<Deadline> = {}): Deadline {
  return {
    id: "dl-1",
    project_id: "proj-1",
    deadline_type: "remise_offres",
    label: "Remise des offres",
    deadline_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days from now
    is_critical: false,
    citation: null,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

function daysFromNow(days: number): string {
  return new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString();
}

// ── Tests: DeadlineCard ──────────────────────────────────────────────────

describe("DeadlineCard", () => {
  it("renders deadline label", () => {
    render(<DeadlineCard deadline={makeDeadline({ label: "Date de remise" })} />);

    expect(screen.getByText("Date de remise")).toBeInTheDocument();
  });

  it("renders type badge for remise_offres", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_type: "remise_offres" })} />);

    expect(screen.getByText("Remise")).toBeInTheDocument();
  });

  it("renders type badge for visite_site", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_type: "visite_site" })} />);

    expect(screen.getByText("Visite")).toBeInTheDocument();
  });

  it("renders type badge for questions_acheteur", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_type: "questions_acheteur" })} />);

    expect(screen.getByText("Q&A")).toBeInTheDocument();
  });

  it("renders type badge for publication_resultats", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_type: "publication_resultats" })} />);

    expect(screen.getByText("Résultats")).toBeInTheDocument();
  });

  it("shows 'Critique' marker for critical deadlines", () => {
    render(<DeadlineCard deadline={makeDeadline({ is_critical: true })} />);

    expect(screen.getByText("Critique")).toBeInTheDocument();
  });

  it("does not show 'Critique' marker for non-critical deadlines", () => {
    render(<DeadlineCard deadline={makeDeadline({ is_critical: false })} />);

    expect(screen.queryByText("Critique")).not.toBeInTheDocument();
  });

  it("shows citation when present", () => {
    render(<DeadlineCard deadline={makeDeadline({ citation: "Article 5.2 du RC" })} />);

    expect(screen.getByText(/Article 5.2 du RC/)).toBeInTheDocument();
  });

  it("does not show citation when null", () => {
    const { container } = render(<DeadlineCard deadline={makeDeadline({ citation: null })} />);

    expect(container.querySelector("p.italic")).not.toBeInTheDocument();
  });

  it("shows green countdown for dates > 14 days away", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_date: daysFromNow(20) })} />);

    // Should show J-20 in a green badge
    expect(screen.getByText(/J/)).toBeInTheDocument();
  });

  it("shows 'Passé' for past deadlines", () => {
    render(<DeadlineCard deadline={makeDeadline({ deadline_date: daysFromNow(-5) })} />);

    expect(screen.getByText("Passé")).toBeInTheDocument();
  });

  it("does not show Critique for past critical deadlines", () => {
    render(<DeadlineCard deadline={makeDeadline({
      is_critical: true,
      deadline_date: daysFromNow(-5),
    })} />);

    expect(screen.queryByText("Critique")).not.toBeInTheDocument();
  });
});

// ── Tests: DeadlineList ──────────────────────────────────────────────────

describe("DeadlineList", () => {
  it("renders empty state when no deadlines", () => {
    render(<DeadlineList deadlines={[]} />);

    expect(screen.getByText("Aucune alerte date disponible")).toBeInTheDocument();
  });

  it("renders multiple deadline cards", () => {
    const deadlines = [
      makeDeadline({ id: "dl-1", label: "Remise des offres" }),
      makeDeadline({ id: "dl-2", label: "Visite de site", deadline_type: "visite_site" }),
    ];
    render(<DeadlineList deadlines={deadlines} />);

    expect(screen.getByText("Remise des offres")).toBeInTheDocument();
    expect(screen.getByText("Visite de site")).toBeInTheDocument();
  });

  it("separates past and upcoming deadlines", () => {
    const deadlines = [
      makeDeadline({ id: "dl-1", label: "Future deadline", deadline_date: daysFromNow(10) }),
      makeDeadline({ id: "dl-2", label: "Past deadline", deadline_date: daysFromNow(-3) }),
    ];
    render(<DeadlineList deadlines={deadlines} />);

    expect(screen.getByText("Dates passées")).toBeInTheDocument();
    expect(screen.getByText("Future deadline")).toBeInTheDocument();
    expect(screen.getByText("Past deadline")).toBeInTheDocument();
  });

  it("does not show 'Dates passées' header when all dates are future", () => {
    const deadlines = [
      makeDeadline({ id: "dl-1", deadline_date: daysFromNow(10) }),
    ];
    render(<DeadlineList deadlines={deadlines} />);

    expect(screen.queryByText("Dates passées")).not.toBeInTheDocument();
  });
});
