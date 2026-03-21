/**
 * Tests for CommandPalette component.
 * Verifies Ctrl+K toggle, keyboard navigation, filtering, and accessibility.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { CommandPalette } from "./CommandPalette";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// ── Setup ─────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
});

// ── Tests ─────────────────────────────────────────────────────────────────

describe("CommandPalette", () => {
  it("is hidden by default", () => {
    render(<CommandPalette />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens on Ctrl+K", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/rechercher une page/i)).toBeInTheDocument();
  });

  it("opens on Cmd+K (Mac)", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", metaKey: true });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("closes on Escape", () => {
    render(<CommandPalette />);

    // Open
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Close
    const input = screen.getByLabelText(/rechercher une page/i);
    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes on backdrop click", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Click backdrop (aria-hidden div)
    const backdrop = document.querySelector("[aria-hidden='true']");
    if (backdrop) fireEvent.click(backdrop);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("shows all navigation items when no query", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    // Check some known items exist
    expect(screen.getByText("Tableau de bord")).toBeInTheDocument();
    expect(screen.getByText("Projets AO")).toBeInTheDocument();
    expect(screen.getByText("Abonnement")).toBeInTheDocument();
    expect(screen.getByText("Développeur")).toBeInTheDocument();
  });

  it("filters items on search query", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const input = screen.getByLabelText(/rechercher une page/i);
    fireEvent.change(input, { target: { value: "pipe" } });

    expect(screen.getByText("Pipeline")).toBeInTheDocument();
    // Other items should be filtered out
    expect(screen.queryByText("Glossaire BTP")).not.toBeInTheDocument();
  });

  it("shows 'no results' when nothing matches", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const input = screen.getByLabelText(/rechercher une page/i);
    fireEvent.change(input, { target: { value: "xyznonexistent" } });

    expect(screen.getByText(/aucun résultat/i)).toBeInTheDocument();
  });

  it("navigates on Enter key", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const input = screen.getByLabelText(/rechercher une page/i);
    // Press Enter on first item (Tableau de bord)
    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("navigates on item click", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const item = screen.getByText("Pipeline");
    fireEvent.click(item);

    expect(mockPush).toHaveBeenCalledWith("/pipeline");
  });

  it("has proper ARIA attributes for accessibility", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-label", "Palette de commandes");
    expect(dialog).toHaveAttribute("aria-modal", "true");

    const input = screen.getByLabelText(/rechercher une page/i);
    expect(input).toHaveAttribute("role", "combobox");
    expect(input).toHaveAttribute("aria-expanded", "true");

    const listbox = screen.getByRole("listbox");
    expect(listbox).toBeInTheDocument();
  });

  it("shows category headers", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    expect(screen.getByText("Navigation")).toBeInTheDocument();
    expect(screen.getByText("Paramètres")).toBeInTheDocument();
  });

  it("arrow down moves to next item", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });

    const input = screen.getByLabelText(/rechercher une page/i);

    // First item should be selected by default
    const firstOption = screen.getAllByRole("option")[0];
    expect(firstOption).toHaveAttribute("aria-selected", "true");

    // Arrow down → second item
    fireEvent.keyDown(input, { key: "ArrowDown" });
    const secondOption = screen.getAllByRole("option")[1];
    expect(secondOption).toHaveAttribute("aria-selected", "true");
  });

  it("toggles off with second Ctrl+K", () => {
    render(<CommandPalette />);

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("clears query on reopen", () => {
    render(<CommandPalette />);

    // Open, type, close, reopen
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    const input = screen.getByLabelText(/rechercher une page/i);
    fireEvent.change(input, { target: { value: "test" } });

    fireEvent.keyDown(window, { key: "k", ctrlKey: true }); // close
    fireEvent.keyDown(window, { key: "k", ctrlKey: true }); // reopen

    const reopenedInput = screen.getByLabelText(/rechercher une page/i);
    expect(reopenedInput).toHaveValue("");
  });
});
