/**
 * Tests for BadgeStatus component.
 * Verifies badge rendering for OK, MANQUANT, A CLARIFIER, and unknown statuses.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BadgeStatus } from "./BadgeStatus";

describe("BadgeStatus", () => {
  it("renders OK badge with green styling", () => {
    const { container } = render(<BadgeStatus status="OK" />);

    expect(screen.getByText("OK")).toBeInTheDocument();
    const badge = container.querySelector(".bg-green-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders MANQUANT badge with red styling", () => {
    const { container } = render(<BadgeStatus status="MANQUANT" />);

    expect(screen.getByText("MANQUANT")).toBeInTheDocument();
    const badge = container.querySelector(".bg-red-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders A CLARIFIER badge with amber styling", () => {
    const { container } = render(<BadgeStatus status="À CLARIFIER" />);

    expect(screen.getByText("À CLARIFIER")).toBeInTheDocument();
    const badge = container.querySelector(".bg-amber-100");
    expect(badge).toBeInTheDocument();
  });

  it("renders unknown status with slate fallback styling", () => {
    const { container } = render(<BadgeStatus status="UNKNOWN" />);

    expect(screen.getByText("UNKNOWN")).toBeInTheDocument();
    const badge = container.querySelector(".bg-slate-100");
    expect(badge).toBeInTheDocument();
  });

  it("has rounded-full class for pill shape", () => {
    const { container } = render(<BadgeStatus status="OK" />);

    const badge = container.querySelector(".rounded-full");
    expect(badge).toBeInTheDocument();
  });

  it("includes border class", () => {
    const { container } = render(<BadgeStatus status="OK" />);

    const badge = container.querySelector(".border");
    expect(badge).toBeInTheDocument();
  });

  it("has correct text for each status", () => {
    const { rerender } = render(<BadgeStatus status="OK" />);
    expect(screen.getByText("OK")).toBeInTheDocument();

    rerender(<BadgeStatus status="MANQUANT" />);
    expect(screen.getByText("MANQUANT")).toBeInTheDocument();

    rerender(<BadgeStatus status="À CLARIFIER" />);
    expect(screen.getByText("À CLARIFIER")).toBeInTheDocument();
  });
});
