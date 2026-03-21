/**
 * Tests for Breadcrumb component.
 * Verifies accessible navigation, JSON-LD structured data, and link rendering.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Breadcrumb } from "./Breadcrumb";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe("Breadcrumb", () => {
  it("renders accessible nav element", () => {
    render(<Breadcrumb items={[{ label: "Projets", href: "/projects" }]} />);

    const nav = screen.getByRole("navigation", { name: /fil d'ariane/i });
    expect(nav).toBeInTheDocument();
  });

  it("renders home icon by default", () => {
    render(<Breadcrumb items={[{ label: "Test" }]} />);

    const homeLink = screen.getByLabelText("Tableau de bord");
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/dashboard");
  });

  it("hides home icon when showHome=false", () => {
    render(<Breadcrumb items={[{ label: "Test" }]} showHome={false} />);

    expect(screen.queryByLabelText("Tableau de bord")).not.toBeInTheDocument();
  });

  it("renders items as links when href provided", () => {
    render(
      <Breadcrumb
        items={[
          { label: "Projets", href: "/projects" },
          { label: "Mon Projet" },
        ]}
      />
    );

    const link = screen.getByText("Projets");
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("href", "/projects");
  });

  it("renders last item as text (not a link)", () => {
    render(
      <Breadcrumb
        items={[
          { label: "Projets", href: "/projects" },
          { label: "Mon Projet" },
        ]}
      />
    );

    const lastItem = screen.getByText("Mon Projet");
    expect(lastItem.tagName).toBe("SPAN");
    expect(lastItem).toHaveAttribute("aria-current", "page");
  });

  it("renders separators between items", () => {
    render(
      <Breadcrumb
        items={[
          { label: "Projets", href: "/projects" },
          { label: "Mon Projet" },
        ]}
      />
    );

    // ChevronRight icons have aria-hidden="true"
    const separators = document.querySelectorAll("[aria-hidden='true']");
    expect(separators.length).toBeGreaterThanOrEqual(2); // home→projects, projects→mon projet
  });

  it("renders empty items array without crash", () => {
    render(<Breadcrumb items={[]} />);

    const nav = screen.getByRole("navigation");
    expect(nav).toBeInTheDocument();
  });

  it("renders single item as current page", () => {
    render(<Breadcrumb items={[{ label: "Dashboard" }]} />);

    const item = screen.getByText("Dashboard");
    expect(item).toHaveAttribute("aria-current", "page");
  });

  it("renders JSON-LD BreadcrumbList schema", () => {
    render(
      <Breadcrumb
        items={[
          { label: "Projets", href: "/projects" },
          { label: "Mon Projet" },
        ]}
      />
    );

    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    expect(scripts.length).toBeGreaterThanOrEqual(1);

    const lastScript = scripts[scripts.length - 1];
    const schema = JSON.parse(lastScript.textContent || "{}");
    expect(schema["@type"]).toBe("BreadcrumbList");
    expect(schema.itemListElement).toHaveLength(3); // Dashboard + Projets + Mon Projet
    expect(schema.itemListElement[0].name).toBe("Tableau de bord");
    expect(schema.itemListElement[1].name).toBe("Projets");
    expect(schema.itemListElement[2].name).toBe("Mon Projet");
  });

  it("JSON-LD uses custom baseUrl", () => {
    render(
      <Breadcrumb
        items={[{ label: "Test", href: "/test" }]}
        baseUrl="https://custom.example.com"
      />
    );

    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    const lastScript = scripts[scripts.length - 1];
    const schema = JSON.parse(lastScript.textContent || "{}");

    expect(schema.itemListElement[0].item).toContain("custom.example.com");
  });
});
