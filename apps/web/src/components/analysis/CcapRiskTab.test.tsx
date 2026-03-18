/**
 * Tests for CcapRiskTab component.
 * Verifies rendering with mock data through AnalysisTabWrapper.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { CcapRiskTab } from "./CcapRiskTab";

// ── Mocks ─────────────────────────────────────────────────────────────────

const mockUseCcapRisks = vi.fn();

vi.mock("@/hooks/useAnalysis", () => ({
  useCcapRisks: (...args: unknown[]) => mockUseCcapRisks(...args),
}));

vi.mock("@/components/ui/AIDisclaimer", () => ({
  default: ({ text }: { text?: string }) => (
    <div data-testid="ai-disclaimer">{text ?? "disclaimer"}</div>
  ),
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function makeQueryResult(overrides: Record<string, unknown>) {
  return {
    data: undefined,
    error: null,
    isLoading: false,
    isError: false,
    isSuccess: false,
    isPending: false,
    isFetching: false,
    isFetched: false,
    isFetchedAfterMount: false,
    isLoadingError: false,
    isRefetchError: false,
    isRefetching: false,
    isStale: false,
    isPlaceholderData: false,
    isInitialLoading: false,
    status: "pending" as const,
    fetchStatus: "idle" as const,
    dataUpdatedAt: 0,
    errorUpdatedAt: 0,
    failureCount: 0,
    failureReason: null,
    errorUpdateCount: 0,
    refetch: vi.fn(),
    promise: Promise.resolve(undefined),
    ...overrides,
  };
}

const MOCK_CCAP_DATA = {
  clauses_risquees: [
    {
      article_reference: "Art. 9.2",
      clause_text: "Penalites de retard de 1/1000e par jour",
      risk_level: "CRITIQUE" as const,
      risk_type: "Penalites excessives",
      conseil: "Negocier un plafond de penalites a 5%",
      citation: "Le montant des penalites est fixe a 1/1000e du marche",
    },
    {
      article_reference: "Art. 15.1",
      clause_text: "Delai de paiement 60 jours",
      risk_level: "HAUT" as const,
      risk_type: "Delai de paiement long",
      conseil: "Verifier conformite avec les regles de la commande publique (30j max)",
      citation: "Le delai de paiement est fixe a 60 jours",
    },
    {
      article_reference: "Art. 22.3",
      clause_text: "Clause de revision des prix",
      risk_level: "BAS" as const,
      risk_type: "Revision favorable",
      conseil: "Clause standard, pas d'action requise",
      citation: "Les prix sont revises selon l'indice BT01",
    },
  ],
  score_risque_global: 72,
  nb_clauses_critiques: 1,
  resume_risques: "Le CCAP presente des clauses de penalites severes et des delais de paiement non conformes.",
  ccap_docs_analyzed: ["CCAP_Marche_2024.pdf"],
};

// ── Tests ─────────────────────────────────────────────────────────────────

describe("CcapRiskTab", () => {
  it("shows loading skeleton when query is loading", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({ isLoading: true })
    );

    const { container } = render(<CcapRiskTab projectId="proj-123" />);

    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows error state when query fails", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({ isError: true, error: new Error("fail") })
    );

    render(<CcapRiskTab projectId="proj-123" />);

    expect(screen.getByText(/Impossible de charger l.analyse des risques CCAP/)).toBeInTheDocument();
  });

  it("renders risk clauses with correct data", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({ isSuccess: true, data: MOCK_CCAP_DATA })
    );

    render(<CcapRiskTab projectId="proj-123" />);

    // Score is rendered
    expect(screen.getByText("72")).toBeInTheDocument();

    // Risk levels badges (appear in both LevelCounter and RiskBadge)
    expect(screen.getAllByText("Critique").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Haut").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Bas").length).toBeGreaterThanOrEqual(1);

    // Risk type titles
    expect(screen.getByText("Penalites excessives")).toBeInTheDocument();
    expect(screen.getByText("Delai de paiement long")).toBeInTheDocument();

    // Article references
    expect(screen.getByText("Art. 9.2")).toBeInTheDocument();
    expect(screen.getByText("Art. 15.1")).toBeInTheDocument();

    // Synthese
    expect(screen.getByText(/penalites severes/)).toBeInTheDocument();

    // AI disclaimer present
    expect(screen.getByTestId("ai-disclaimer")).toBeInTheDocument();
  });

  it("shows no-CCAP message when no_ccap_document is true", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({
        isSuccess: true,
        data: {
          clauses_risquees: [],
          score_risque_global: 0,
          nb_clauses_critiques: 0,
          resume_risques: "",
          no_ccap_document: true,
          message: "Aucun fichier CCAP dans le DCE.",
        },
      })
    );

    render(<CcapRiskTab projectId="proj-123" />);

    expect(screen.getByText("Aucun document CCAP disponible")).toBeInTheDocument();
    expect(screen.getByText("Aucun fichier CCAP dans le DCE.")).toBeInTheDocument();
  });

  it("shows zero-risk state when clauses_risquees is empty", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({
        isSuccess: true,
        data: {
          clauses_risquees: [],
          score_risque_global: 0,
          nb_clauses_critiques: 0,
          resume_risques: "",
          ccap_docs_analyzed: ["CCAP.pdf"],
        },
      })
    );

    render(<CcapRiskTab projectId="proj-123" />);

    expect(screen.getByText("Aucune clause risquée détectée")).toBeInTheDocument();
  });

  it("passes projectId to useCcapRisks hook", () => {
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({ isLoading: true })
    );

    render(<CcapRiskTab projectId="my-project-42" />);

    expect(mockUseCcapRisks).toHaveBeenCalledWith("my-project-42");
  });

  it("renders clauses sorted by severity (CRITIQUE first)", () => {
    const data = {
      ...MOCK_CCAP_DATA,
      clauses_risquees: [
        { ...MOCK_CCAP_DATA.clauses_risquees[2] }, // BAS
        { ...MOCK_CCAP_DATA.clauses_risquees[0] }, // CRITIQUE
        { ...MOCK_CCAP_DATA.clauses_risquees[1] }, // HAUT
      ],
    };
    mockUseCcapRisks.mockReturnValue(
      makeQueryResult({ isSuccess: true, data })
    );

    render(<CcapRiskTab projectId="proj-123" />);

    // All three risk types present - article refs shown
    const articleRefs = screen.getAllByText(/Art\./);
    expect(articleRefs.length).toBe(3);

    // CRITIQUE clause (Art. 9.2) should appear first by index "1"
    // The sorted order is CRITIQUE, HAUT, BAS
    const riskTypes = screen.getAllByText(/Penalites excessives|Delai de paiement long|Revision favorable/);
    expect(riskTypes[0]).toHaveTextContent("Penalites excessives");
    expect(riskTypes[1]).toHaveTextContent("Delai de paiement long");
    expect(riskTypes[2]).toHaveTextContent("Revision favorable");
  });
});
