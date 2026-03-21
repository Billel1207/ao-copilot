"use client";

import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  /** Show home icon as first item */
  showHome?: boolean;
  /** Base URL for JSON-LD structured data (default: https://aocopilot.fr) */
  baseUrl?: string;
}

/**
 * Generate BreadcrumbList JSON-LD for SEO (schema.org).
 * Google displays this as a navigation trail in search results.
 *
 * Security note: Data is built from static labels and hrefs defined
 * in our own components — no user input is interpolated.
 * JSON.stringify safely escapes all values. This is the standard
 * Next.js pattern for JSON-LD (same as components/seo/JsonLd.tsx).
 */
function BreadcrumbJsonLd({ items, baseUrl = "https://aocopilot.fr" }: { items: BreadcrumbItem[]; baseUrl?: string }) {
  const allItems = [
    { label: "Tableau de bord", href: "/dashboard" },
    ...items,
  ];

  const schema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: allItems.map((item, index) => {
      const entry: Record<string, unknown> = {
        "@type": "ListItem",
        position: index + 1,
        name: item.label,
      };
      if (item.href) {
        entry.item = `${baseUrl}${item.href}`;
      }
      return entry;
    }),
  };

  return (
    <script
      type="application/ld+json"
      // Safe: schema is built from static labels/hrefs, not user input.
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

/**
 * Accessible breadcrumb navigation (WCAG 2.4.8).
 *
 * Usage:
 *   <Breadcrumb items={[
 *     { label: "Projets", href: "/projects" },
 *     { label: "Mon Projet" },
 *   ]} />
 */
export function Breadcrumb({ items, showHome = true, baseUrl }: BreadcrumbProps) {
  return (
    <>
    <BreadcrumbJsonLd items={items} baseUrl={baseUrl} />
    <nav aria-label="Fil d'Ariane" className="flex items-center gap-1 text-sm">
      {showHome && (
        <>
          <Link
            href="/dashboard"
            className="text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors p-1"
            aria-label="Tableau de bord"
          >
            <Home className="w-3.5 h-3.5" />
          </Link>
          {items.length > 0 && (
            <ChevronRight className="w-3 h-3 text-slate-300 dark:text-slate-600 flex-shrink-0" aria-hidden="true" />
          )}
        </>
      )}

      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={index} className="flex items-center gap-1">
            {isLast || !item.href ? (
              <span
                className="text-slate-700 dark:text-slate-200 font-medium truncate max-w-[200px]"
                aria-current="page"
              >
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href}
                className="text-slate-400 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors truncate max-w-[200px]"
              >
                {item.label}
              </Link>
            )}
            {!isLast && (
              <ChevronRight className="w-3 h-3 text-slate-300 dark:text-slate-600 flex-shrink-0" aria-hidden="true" />
            )}
          </span>
        );
      })}
    </nav>
    </>
  );
}

export default Breadcrumb;
