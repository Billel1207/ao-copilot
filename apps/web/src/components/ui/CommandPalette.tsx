"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard, FolderOpen, Kanban, Bell, BookOpen,
  BarChart3, BookText, CreditCard, Building2, Users,
  Code, Search, ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

/** A single command entry in the palette. */
interface CommandItem {
  id: string;
  label: string;
  href: string;
  icon: React.ElementType;
  category: "Navigation" | "Paramètres";
  keywords?: string[];
}

const COMMANDS: CommandItem[] = [
  // ── Navigation principale ──
  { id: "dashboard",   label: "Tableau de bord",  href: "/dashboard",  icon: LayoutDashboard, category: "Navigation" },
  { id: "projects",    label: "Projets AO",       href: "/projects",   icon: FolderOpen,      category: "Navigation", keywords: ["appels", "offres", "dce"] },
  { id: "pipeline",    label: "Pipeline",          href: "/pipeline",   icon: Kanban,          category: "Navigation", keywords: ["kanban", "suivi"] },
  { id: "veille",      label: "Veille AO",         href: "/veille",     icon: Bell,            category: "Navigation", keywords: ["alertes", "ted", "boamp"] },
  { id: "library",     label: "Bibliothèque",      href: "/library",    icon: BookOpen,        category: "Navigation", keywords: ["snippets", "modèles"] },
  { id: "analytics",   label: "Analytics",          href: "/analytics",  icon: BarChart3,       category: "Navigation", keywords: ["stats", "graphiques"] },
  { id: "glossaire",   label: "Glossaire BTP",      href: "/glossaire",  icon: BookText,        category: "Navigation", keywords: ["termes", "définitions", "ccag"] },
  { id: "billing",     label: "Abonnement",         href: "/billing",    icon: CreditCard,      category: "Navigation", keywords: ["plan", "facturation", "stripe"] },
  // ── Paramètres ──
  { id: "company",     label: "Mon entreprise",     href: "/settings/company",   icon: Building2, category: "Paramètres", keywords: ["profil", "siret", "certifications"] },
  { id: "team",        label: "Équipe",              href: "/settings/team",      icon: Users,     category: "Paramètres", keywords: ["membres", "invitations"] },
  { id: "developer",   label: "Développeur",         href: "/settings/developer", icon: Code,      category: "Paramètres", keywords: ["api", "webhooks", "clés"] },
];

/**
 * Global command palette — Ctrl+K / Cmd+K to open.
 *
 * Accessibility: focus trap, arrow key navigation, Escape to close,
 * aria-role="dialog" + aria-label + listbox semantics.
 */
export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // ── Global keyboard shortcut ──
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
      // Small delay for the DOM to render
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  // ── Fuzzy filter ──
  const filtered = useMemo(() => {
    if (!query.trim()) return COMMANDS;
    const q = query.toLowerCase();
    return COMMANDS.filter((cmd) => {
      const haystack = [cmd.label, ...(cmd.keywords ?? [])].join(" ").toLowerCase();
      return q.split("").every((char) => haystack.includes(char)) &&
        haystack.includes(q.charAt(0));
    });
  }, [query]);

  // Reset active index when results change
  useEffect(() => {
    setActiveIndex(0);
  }, [filtered.length]);

  // ── Navigate ──
  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  // ── Keyboard navigation inside palette ──
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => (i + 1) % Math.max(filtered.length, 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => (i - 1 + filtered.length) % Math.max(filtered.length, 1));
      } else if (e.key === "Enter" && filtered[activeIndex]) {
        e.preventDefault();
        navigate(filtered[activeIndex].href);
      }
    },
    [filtered, activeIndex, navigate],
  );

  // Scroll active item into view
  useEffect(() => {
    const el = listRef.current?.querySelector(`[data-index="${activeIndex}"]`);
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  if (!open) return null;

  // Group by category
  const grouped = filtered.reduce<Record<string, CommandItem[]>>((acc, cmd) => {
    (acc[cmd.category] ??= []).push(cmd);
    return acc;
  }, {});

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[60] bg-slate-900/50 backdrop-blur-sm"
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-label="Palette de commandes"
        aria-modal="true"
        className="fixed inset-0 z-[61] flex items-start justify-center pt-[15vh]"
        onKeyDown={handleKeyDown}
      >
        <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
            <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Rechercher une page…"
              className="flex-1 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 outline-none"
              aria-label="Rechercher une page"
              role="combobox"
              aria-expanded="true"
              aria-controls="command-list"
              aria-activedescendant={filtered[activeIndex] ? `cmd-${filtered[activeIndex].id}` : undefined}
            />
            <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 bg-slate-100 dark:bg-slate-800 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div
            id="command-list"
            ref={listRef}
            role="listbox"
            className="max-h-[320px] overflow-y-auto py-2"
          >
            {filtered.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-slate-400">
                Aucun résultat pour &quot;{query}&quot;
              </p>
            ) : (
              Object.entries(grouped).map(([category, items]) => (
                <div key={category}>
                  <p className="px-4 py-1.5 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    {category}
                  </p>
                  {items.map((cmd) => {
                    const globalIdx = filtered.indexOf(cmd);
                    const isActive = globalIdx === activeIndex;
                    const Icon = cmd.icon;

                    return (
                      <button
                        key={cmd.id}
                        id={`cmd-${cmd.id}`}
                        role="option"
                        aria-selected={isActive}
                        data-index={globalIdx}
                        onClick={() => navigate(cmd.href)}
                        onMouseEnter={() => setActiveIndex(globalIdx)}
                        className={cn(
                          "w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors",
                          isActive
                            ? "bg-primary-50 dark:bg-primary-900/30 text-primary-800 dark:text-primary-200"
                            : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800",
                        )}
                      >
                        <Icon className={cn("w-4 h-4 flex-shrink-0", isActive ? "text-primary-600" : "text-slate-400")} />
                        <span className="flex-1 text-left">{cmd.label}</span>
                        {isActive && <ArrowRight className="w-3 h-3 text-primary-400" />}
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800 flex items-center gap-4 text-[10px] text-slate-400">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-[9px]">↑↓</kbd>
              naviguer
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-[9px]">↵</kbd>
              ouvrir
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-[9px]">esc</kbd>
              fermer
            </span>
          </div>
        </div>
      </div>
    </>
  );
}

export default CommandPalette;
