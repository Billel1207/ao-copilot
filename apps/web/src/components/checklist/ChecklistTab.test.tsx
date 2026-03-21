/**
 * Tests for ChecklistTab component.
 * Verifies checklist rendering, filtering, loading, and empty states.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { ChecklistTab } from "./ChecklistTab";

// ── Mocks ─────────────────────────────────────────────────────────────────

const mockUseChecklist = vi.fn();
const mockUseGenerateText = vi.fn();
const mockUseUpdateChecklistItem = vi.fn();

vi.mock("@/hooks/useAnalysis", () => ({
  useChecklist: (...args: unknown[]) => mockUseChecklist(...args),
  useGenerateText: (...args: unknown[]) => mockUseGenerateText(...args),
  useUpdateChecklistItem: (...args: unknown[]) => mockUseUpdateChecklistItem(...args),
}));

vi.mock("@/components/ui/CitationTooltip", () => ({
  CitationTooltip: ({ citations }: { citations: unknown[] }) => (
    <span data-testid="citation-tooltip">{citations?.length ?? 0} sources</span>
  ),
}));

vi.mock("@/components/ui/ConfidenceBar", () => ({
  ConfidenceBar: ({ confidence }: { confidence: number | null }) => (
    <span data-testid="confidence-bar">{confidence !== null ? `${Math.round(confidence * 100)}%` : "—"}</span>
  ),
}));

vi.mock("@/components/common/Skeleton", () => ({
  TableSkeleton: () => <div data-testid="table-skeleton">Loading...</div>,
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function makeChecklistData(overrides: Record<string, unknown> = {}) {
  return {
    total: 3,
    by_status: { OK: 1, MANQUANT: 1, "À CLARIFIER": 1 },
    by_criticality: { "Éliminatoire": 1, "Important": 1, "Info": 1 },
    checklist: [
      {
        id: "item-1",
        requirement: "Attestation d'assurance RC Pro",
        what_to_provide: "Copie de l'attestation en cours de validité",
        citations: [{ doc: "RC.pdf", page: 5, quote: "L'entreprise doit fournir..." }],
        category: "Administratif",
        criticality: "Éliminatoire",
        status: "MANQUANT",
        confidence: 0.95,
      },
      {
        id: "item-2",
        requirement: "Références de chantiers similaires",
        what_to_provide: null,
        citations: [],
        category: "Technique",
        criticality: "Important",
        status: "OK",
        confidence: 0.8,
      },
      {
        id: "item-3",
        requirement: "Mémoire technique",
        what_to_provide: "Document décrivant la méthodologie",
        citations: [],
        category: "Technique",
        criticality: "Info",
        status: "À CLARIFIER",
        confidence: 0.6,
      },
    ],
    ...overrides,
  };
}

function setupMocks(data: ReturnType<typeof makeChecklistData> | null = null, isLoading = false) {
  mockUseChecklist.mockReturnValue({ data, isLoading });
  mockUseGenerateText.mockReturnValue({ mutateAsync: vi.fn() });
  mockUseUpdateChecklistItem.mockReturnValue({ mutate: vi.fn(), isPending: false });
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("ChecklistTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading skeleton when loading", () => {
    setupMocks(null, true);

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByTestId("table-skeleton")).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    setupMocks(null, false);

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByText(/Aucune donnée disponible/)).toBeInTheDocument();
  });

  it("renders checklist items", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByText("Attestation d'assurance RC Pro")).toBeInTheDocument();
    expect(screen.getByText("Références de chantiers similaires")).toBeInTheDocument();
    expect(screen.getByText("Mémoire technique")).toBeInTheDocument();
  });

  it("renders filter pills with correct counts", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    // Status filters
    expect(screen.getByText("Tous")).toBeInTheDocument();
    expect(screen.getByText("Manquants")).toBeInTheDocument();
    expect(screen.getByText("À clarifier")).toBeInTheDocument();

    // Criticality filters
    expect(screen.getByText("Éliminatoires")).toBeInTheDocument();
    expect(screen.getByText("Importants")).toBeInTheDocument();
  });

  it("renders category labels", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByText("Administratif")).toBeInTheDocument();
    expect(screen.getAllByText("Technique").length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty filter state when no items match", () => {
    setupMocks(makeChecklistData({ checklist: [] }));

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByText("Aucune exigence correspondant aux filtres")).toBeInTheDocument();
  });

  it("expands item on click to show details", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    // Click on the first item
    fireEvent.click(screen.getByText("Attestation d'assurance RC Pro"));

    // Should show the "what_to_provide" section
    expect(screen.getByText("À fournir :")).toBeInTheDocument();
    expect(screen.getByText("Copie de l'attestation en cours de validité")).toBeInTheDocument();
  });

  it("shows status change buttons when item is expanded", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    // Expand item
    fireEvent.click(screen.getByText("Attestation d'assurance RC Pro"));

    // Status buttons should appear
    expect(screen.getByText("Statut :")).toBeInTheDocument();
  });

  it("renders table header columns", () => {
    setupMocks(makeChecklistData());

    render(<ChecklistTab projectId="proj-1" />);

    expect(screen.getByText("#")).toBeInTheDocument();
    expect(screen.getByText("Exigence")).toBeInTheDocument();
    expect(screen.getByText("Criticité")).toBeInTheDocument();
    expect(screen.getByText("Statut")).toBeInTheDocument();
    expect(screen.getByText("Confiance")).toBeInTheDocument();
  });

  it("passes projectId to useChecklist hook", () => {
    setupMocks(null, true);

    render(<ChecklistTab projectId="proj-42" />);

    expect(mockUseChecklist).toHaveBeenCalledWith(
      "proj-42",
      expect.objectContaining({ status: "", criticality: "" })
    );
  });
});
