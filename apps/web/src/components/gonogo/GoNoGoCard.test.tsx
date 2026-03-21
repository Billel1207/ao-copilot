/**
 * Tests for GoNoGoCard component.
 * Verifies GO/ATTENTION/NO-GO states, score rendering, loading, and error states.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { GoNoGoCard } from "./GoNoGoCard";

// ── Mocks ─────────────────────────────────────────────────────────────────

const mockUseGoNoGo = vi.fn();

vi.mock("@/hooks/useAnalysis", () => ({
  useGoNoGo: (...args: unknown[]) => mockUseGoNoGo(...args),
}));

vi.mock("lucide-react", async () => {
  const actual = await vi.importActual("lucide-react") as Record<string, unknown>;
  return {
    ...actual,
    Loader2: (props: { className?: string }) => <span data-testid="loader" className={props.className} />,
  };
});

// ── Helpers ───────────────────────────────────────────────────────────────

function makeGoNoGoData(overrides: Record<string, unknown> = {}) {
  return {
    score: 75,
    recommendation: "GO",
    strengths: ["Bonne capacité technique", "Références solides"],
    risks: ["Délais serrés"],
    summary: "Le projet est favorable.",
    breakdown: {
      technical_fit: 80,
      financial_capacity: 70,
      timeline_feasibility: 60,
      competitive_position: 85,
    },
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("GoNoGoCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state", () => {
    mockUseGoNoGo.mockReturnValue({ data: null, isLoading: true, error: null });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText(/Chargement du score Go\/No-Go/)).toBeInTheDocument();
  });

  it("shows error state when data is null", () => {
    mockUseGoNoGo.mockReturnValue({ data: null, isLoading: false, error: null });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText(/Score Go\/No-Go non disponible/)).toBeInTheDocument();
  });

  it("shows error state on error", () => {
    mockUseGoNoGo.mockReturnValue({ data: null, isLoading: false, error: new Error("fail") });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText(/Score Go\/No-Go non disponible/)).toBeInTheDocument();
  });

  it("renders GO state with score >= 70", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData({ score: 82, recommendation: "GO" }),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText("GO")).toBeInTheDocument();
    // Score circle has role="meter"
    const meter = screen.getByRole("meter");
    expect(meter).toHaveAttribute("aria-valuenow", "82");
    expect(meter).toHaveAttribute("aria-label", "Score Go/No-Go : 82 sur 100");
  });

  it("renders NO-GO state with score < 40", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData({ score: 25, recommendation: "NO-GO" }),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText("NO-GO")).toBeInTheDocument();
  });

  it("renders ATTENTION state for mid-range score", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData({ score: 55, recommendation: "ATTENTION" }),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText("ATTENTION")).toBeInTheDocument();
  });

  it("renders summary text", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData({ summary: "Projet favorable avec quelques risques." }),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText("Projet favorable avec quelques risques.")).toBeInTheDocument();
  });

  it("renders strengths and risks lists", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData({
        strengths: ["Point fort 1", "Point fort 2"],
        risks: ["Risque A"],
      }),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    expect(screen.getByText("Points forts")).toBeInTheDocument();
    expect(screen.getByText("Risques")).toBeInTheDocument();
    expect(screen.getByText("Point fort 1")).toBeInTheDocument();
    expect(screen.getByText("Point fort 2")).toBeInTheDocument();
    expect(screen.getByText("Risque A")).toBeInTheDocument();
  });

  it("renders dimension breakdown bars", () => {
    mockUseGoNoGo.mockReturnValue({
      data: makeGoNoGoData(),
      isLoading: false,
      error: null,
    });

    render(<GoNoGoCard projectId="proj-1" />);

    const progressBars = screen.getAllByRole("progressbar");
    expect(progressBars).toHaveLength(4);
    expect(screen.getByText("Adéquation technique")).toBeInTheDocument();
    expect(screen.getByText("Capacité financière")).toBeInTheDocument();
    expect(screen.getByText("Faisabilité délais")).toBeInTheDocument();
    expect(screen.getByText("Position concurrentielle")).toBeInTheDocument();
  });

  it("passes projectId to useGoNoGo hook", () => {
    mockUseGoNoGo.mockReturnValue({ data: null, isLoading: true, error: null });

    render(<GoNoGoCard projectId="my-project-99" />);

    expect(mockUseGoNoGo).toHaveBeenCalledWith("my-project-99", true);
  });
});
