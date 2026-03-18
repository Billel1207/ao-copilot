/**
 * Tests for DarkModeToggle component.
 * Verifies dark class toggling on documentElement and localStorage persistence.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import DarkModeToggle from "./DarkModeToggle";

// ── localStorage mock ────────────────────────────────────────────────────
const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
    get length() { return Object.keys(store).length; },
    key: vi.fn((i: number) => Object.keys(store)[i] ?? null),
  };
})();
Object.defineProperty(globalThis, "localStorage", { value: storageMock, writable: true });

// ── Setup ─────────────────────────────────────────────────────────────────

beforeEach(() => {
  document.documentElement.classList.remove("dark");
  storageMock.clear();
  vi.clearAllMocks();
  // Default matchMedia mock (light mode)
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
});

// ── Tests ─────────────────────────────────────────────────────────────────

describe("DarkModeToggle", () => {
  it("renders a toggle button with accessible label", () => {
    render(<DarkModeToggle />);

    const button = screen.getByRole("button", { name: /basculer mode sombre/i });
    expect(button).toBeInTheDocument();
  });

  it("starts in light mode by default when no localStorage or prefers-color-scheme", () => {
    // Mock matchMedia to return false for dark preference
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    expect(document.documentElement.classList.contains("dark")).toBe(false);
    // Title should indicate "Mode sombre" (offering to switch TO dark)
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Mode sombre");
  });

  it("adds dark class on click and persists in localStorage", () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("ao-theme")).toBe("dark");
  });

  it("removes dark class on second click and persists light in localStorage", () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    const button = screen.getByRole("button");

    // First click -> dark
    fireEvent.click(button);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(localStorage.getItem("ao-theme")).toBe("dark");

    // Second click -> light
    fireEvent.click(button);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(localStorage.getItem("ao-theme")).toBe("light");
  });

  it("initializes in dark mode when localStorage has 'dark'", () => {
    localStorage.setItem("ao-theme", "dark");

    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Mode clair");
  });

  it("initializes in dark mode when system prefers dark and no localStorage", () => {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-color-scheme: dark)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    expect(document.documentElement.classList.contains("dark")).toBe(true);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Mode clair");
  });

  it("stays light when localStorage is 'light' even if system prefers dark", () => {
    localStorage.setItem("ao-theme", "light");

    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-color-scheme: dark)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<DarkModeToggle />);

    // The component checks: stored === "dark" || (!stored && matchMedia)
    // stored = "light", so first condition false, second condition (!stored) false
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
