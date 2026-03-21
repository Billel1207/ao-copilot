/**
 * Tests for ExportTab component.
 * Verifies export buttons, plan restrictions, and ready/not-ready states.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ExportTab } from "./ExportTab";

// ── Mocks ─────────────────────────────────────────────────────────────────

vi.mock("@/lib/api", () => ({
  exportApi: {
    startPdf: vi.fn(),
    startWord: vi.fn(),
    startMemo: vi.fn(),
    startDpgfExcel: vi.fn(),
    getStatus: vi.fn(),
  },
}));

vi.mock("lucide-react", async () => {
  const actual = await vi.importActual("lucide-react") as Record<string, unknown>;
  return {
    ...actual,
    // Keep all icons as simple spans for testing
  };
});

// ── Tests ─────────────────────────────────────────────────────────────────

describe("ExportTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders export section header", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" />);

    expect(screen.getByText("Exporter le rapport")).toBeInTheDocument();
    expect(screen.getByText(/Générez votre rapport complet/)).toBeInTheDocument();
  });

  it("renders PDF and Word export cards", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="pro" />);

    expect(screen.getByText("Rapport PDF")).toBeInTheDocument();
    expect(screen.getByText("Rapport Word")).toBeInTheDocument();
  });

  it("renders Mémoire Technique card", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="pro" />);

    expect(screen.getByText("Mémoire Technique")).toBeInTheDocument();
  });

  it("shows warning when analysis is not ready", () => {
    render(<ExportTab projectId="proj-1" projectStatus="pending" />);

    expect(screen.getByText(/analyse doit être terminée pour pouvoir exporter/)).toBeInTheDocument();
  });

  it("does not show warning when analysis is ready", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" />);

    expect(screen.queryByText(/analyse doit être terminée pour pouvoir exporter/)).not.toBeInTheDocument();
  });

  it("disables PDF button when project is not ready", () => {
    render(<ExportTab projectId="proj-1" projectStatus="pending" userPlan="starter" />);

    const pdfBtn = screen.getByText("Générer le PDF");
    expect(pdfBtn).toBeDisabled();
  });

  it("enables PDF button when project is ready", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="starter" />);

    const pdfBtn = screen.getByText("Générer le PDF");
    expect(pdfBtn).not.toBeDisabled();
  });

  it("locks Word export for non-pro plans", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="starter" />);

    // The lock overlay shows "Plan Pro requis"
    expect(screen.getAllByText("Plan Pro requis").length).toBeGreaterThanOrEqual(1);
  });

  it("unlocks Word export for pro plan", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="pro" />);

    const wordBtn = screen.getByText("Générer le Word");
    expect(wordBtn).not.toBeDisabled();
  });

  it("shows DPGF Excel card when hasDpgfDocs is true", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="pro" hasDpgfDocs />);

    expect(screen.getByText("DPGF / BPU en Excel")).toBeInTheDocument();
    expect(screen.getByText("Exporter DPGF en Excel")).toBeInTheDocument();
  });

  it("hides DPGF Excel card when hasDpgfDocs is false", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="pro" hasDpgfDocs={false} />);

    expect(screen.queryByText("DPGF / BPU en Excel")).not.toBeInTheDocument();
  });

  it("lists PDF features", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="starter" />);

    expect(screen.getByText("Résumé exécutif mis en page")).toBeInTheDocument();
    expect(screen.getByText("Disponible sur tous les plans")).toBeInTheDocument();
  });

  it("shows upgrade link for locked exports", () => {
    render(<ExportTab projectId="proj-1" projectStatus="ready" userPlan="starter" />);

    const upgradeLinks = screen.getAllByText("Passer au Pro");
    expect(upgradeLinks.length).toBeGreaterThanOrEqual(1);
  });
});
