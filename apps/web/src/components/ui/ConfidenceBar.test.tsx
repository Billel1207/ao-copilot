/**
 * Tests for ConfidenceBar component.
 * Verifies percentage display, color ranges, and null handling.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ConfidenceBar } from "./ConfidenceBar";

describe("ConfidenceBar", () => {
  it("renders percentage label for high confidence", () => {
    render(<ConfidenceBar confidence={0.92} />);

    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("renders percentage label for medium confidence", () => {
    render(<ConfidenceBar confidence={0.65} />);

    expect(screen.getByText("65%")).toBeInTheDocument();
  });

  it("renders percentage label for low confidence", () => {
    render(<ConfidenceBar confidence={0.3} />);

    expect(screen.getByText("30%")).toBeInTheDocument();
  });

  it("returns null when confidence is null", () => {
    const { container } = render(<ConfidenceBar confidence={null} />);

    expect(container.innerHTML).toBe("");
  });

  it("returns null when confidence is undefined", () => {
    const { container } = render(<ConfidenceBar confidence={undefined as unknown as null} />);

    expect(container.innerHTML).toBe("");
  });

  it("hides label when showLabel is false", () => {
    const { container } = render(<ConfidenceBar confidence={0.85} showLabel={false} />);

    expect(screen.queryByText("85%")).not.toBeInTheDocument();
    // But the bar should still render
    expect(container.querySelector("div")).toBeInTheDocument();
  });

  it("applies green color for confidence >= 80%", () => {
    const { container } = render(<ConfidenceBar confidence={0.85} />);

    const bar = container.querySelector(".bg-green-500");
    expect(bar).toBeInTheDocument();
  });

  it("applies amber color for confidence >= 60% and < 80%", () => {
    const { container } = render(<ConfidenceBar confidence={0.7} />);

    const bar = container.querySelector(".bg-amber-400");
    expect(bar).toBeInTheDocument();
  });

  it("applies red color for confidence < 60%", () => {
    const { container } = render(<ConfidenceBar confidence={0.4} />);

    const bar = container.querySelector(".bg-red-400");
    expect(bar).toBeInTheDocument();
  });

  it("rounds percentage correctly", () => {
    render(<ConfidenceBar confidence={0.876} />);

    expect(screen.getByText("88%")).toBeInTheDocument();
  });
});
