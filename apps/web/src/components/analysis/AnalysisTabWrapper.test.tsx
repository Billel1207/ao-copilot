/**
 * Tests for AnalysisTabWrapper component.
 * Verifies rendering for loading, error, empty, and data states.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { AnalysisTabWrapper } from "./AnalysisTabWrapper";
import { type UseQueryResult } from "@tanstack/react-query";

// ── Mocks ─────────────────────────────────────────────────────────────────

vi.mock("@/components/ui/AIDisclaimer", () => ({
  default: ({ text }: { text?: string }) => (
    <div data-testid="ai-disclaimer">
      {text ?? "Aide à la décision générée par intelligence artificielle"}
    </div>
  ),
}));

// ── Helpers ───────────────────────────────────────────────────────────────

function makeQuery<T>(overrides: Partial<UseQueryResult<T, unknown>>): UseQueryResult<T, unknown> {
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
    status: "pending",
    fetchStatus: "idle",
    dataUpdatedAt: 0,
    errorUpdatedAt: 0,
    failureCount: 0,
    failureReason: null,
    errorUpdateCount: 0,
    refetch: vi.fn(),
    promise: Promise.resolve({} as T),
    ...overrides,
  } as UseQueryResult<T, unknown>;
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("AnalysisTabWrapper", () => {
  it("shows default skeleton when loading", () => {
    const query = makeQuery<string>({ isLoading: true });

    const { container } = render(
      <AnalysisTabWrapper query={query}>
        {(data) => <div data-testid="content">{data}</div>}
      </AnalysisTabWrapper>
    );

    // Default skeleton has animate-pulse class
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
    // Children should NOT be rendered
    expect(screen.queryByTestId("content")).not.toBeInTheDocument();
  });

  it("shows custom skeleton when loading and skeleton prop provided", () => {
    const query = makeQuery<string>({ isLoading: true });

    render(
      <AnalysisTabWrapper
        query={query}
        skeleton={<div data-testid="custom-skeleton">Loading...</div>}
      >
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByTestId("custom-skeleton")).toBeInTheDocument();
  });

  it("shows error message with AlertTriangle when query fails", () => {
    const query = makeQuery<string>({ isError: true, error: new Error("fail") });

    render(
      <AnalysisTabWrapper query={query} errorMessage="Erreur de chargement.">
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByText("Erreur de chargement.")).toBeInTheDocument();
    expect(
      screen.getByText(/Vérifiez que l.analyse du projet a bien été lancée/)
    ).toBeInTheDocument();
    expect(screen.queryByTestId("ai-disclaimer")).not.toBeInTheDocument();
  });

  it("shows default error message when no custom errorMessage provided", () => {
    const query = makeQuery<string>({ isError: true, error: new Error("fail") });

    render(
      <AnalysisTabWrapper query={query}>
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByText("Impossible de charger cette analyse.")).toBeInTheDocument();
  });

  it("shows empty message when data is null", () => {
    const query = makeQuery<string | null>({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: null as unknown as undefined,
    });

    render(
      <AnalysisTabWrapper query={query as UseQueryResult<string, unknown>} emptyMessage="Pas de donnees.">
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByText("Pas de donnees.")).toBeInTheDocument();
  });

  it("shows default empty message when no custom emptyMessage provided", () => {
    const query = makeQuery<string>({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: undefined,
    });

    render(
      <AnalysisTabWrapper query={query}>
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByText("Aucune donnée disponible.")).toBeInTheDocument();
  });

  it("renders children with data and AIDisclaimer when data is available", () => {
    const query = makeQuery<{ message: string }>({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: { message: "Resultats analyse" },
    });

    render(
      <AnalysisTabWrapper query={query}>
        {(data) => <div data-testid="content">{data.message}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByTestId("content")).toHaveTextContent("Resultats analyse");
    expect(screen.getByTestId("ai-disclaimer")).toBeInTheDocument();
  });

  it("passes custom disclaimerText to AIDisclaimer", () => {
    const query = makeQuery<string>({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: "ok",
    });

    render(
      <AnalysisTabWrapper query={query} disclaimerText="Texte personnalise">
        {(data) => <div>{data}</div>}
      </AnalysisTabWrapper>
    );

    expect(screen.getByTestId("ai-disclaimer")).toHaveTextContent("Texte personnalise");
  });
});
