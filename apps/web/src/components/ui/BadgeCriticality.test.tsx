/**
 * Tests for BadgeCriticality component.
 * Verifies badge rendering for each criticality level and null handling.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BadgeCriticality } from "./BadgeCriticality";

describe("BadgeCriticality", () => {
  it("renders 'Éliminatoire' with red styling and dot", () => {
    const { container } = render(<BadgeCriticality criticality="Éliminatoire" />);

    expect(screen.getByText("Éliminatoire")).toBeInTheDocument();
    const badge = container.querySelector(".bg-red-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders 'Important' with amber styling and dot", () => {
    const { container } = render(<BadgeCriticality criticality="Important" />);

    expect(screen.getByText("Important")).toBeInTheDocument();
    const badge = container.querySelector(".bg-amber-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders 'Info' with slate styling", () => {
    const { container } = render(<BadgeCriticality criticality="Info" />);

    expect(screen.getByText("Info")).toBeInTheDocument();
    const badge = container.querySelector(".bg-slate-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders dash when criticality is null", () => {
    render(<BadgeCriticality criticality={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("falls back to Info styling for unknown criticality", () => {
    const { container } = render(<BadgeCriticality criticality="Unknown" />);

    expect(screen.getByText("Unknown")).toBeInTheDocument();
    // Falls back to Info config (bg-slate-100)
    const badge = container.querySelector(".bg-slate-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders small size variant", () => {
    const { container } = render(<BadgeCriticality criticality="Important" size="sm" />);

    const badge = container.querySelector(".px-2");
    expect(badge).toBeInTheDocument();
  });

  it("renders default size variant", () => {
    const { container } = render(<BadgeCriticality criticality="Important" size="default" />);

    const badge = container.querySelector(".px-2\\.5");
    expect(badge).toBeInTheDocument();
  });
});
