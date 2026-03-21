"use client";

import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  /** Tab name for error reporting */
  tabName?: string;
  /** Fallback UI — if omitted, a default error card is shown */
  fallback?: ReactNode;
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary scoped to a single analysis tab.
 *
 * If one tab crashes (malformed data, rendering error), only that tab shows
 * an error — the other 17 tabs remain fully functional.
 *
 * Usage:
 *   <TabErrorBoundary tabName="CCAP">
 *     <CcapRiskTab ... />
 *   </TabErrorBoundary>
 */
export class TabErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Report to Sentry if available
    if (typeof window !== "undefined" && (window as any).__SENTRY__) {
      try {
        const Sentry = require("@sentry/nextjs");
        Sentry.captureException(error, {
          tags: { component: "TabErrorBoundary", tab: this.props.tabName },
          extra: { componentStack: errorInfo.componentStack },
        });
      } catch {
        // Sentry not available — silent
      }
    }
    console.error(`[TabErrorBoundary:${this.props.tabName}]`, error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          role="alert"
          className="card p-8 flex flex-col items-center gap-4 text-center animate-fade-in"
        >
          <div className="w-12 h-12 rounded-full bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-amber-500" aria-hidden="true" />
          </div>
          <div>
            <p className="text-slate-700 dark:text-slate-300 font-semibold mb-1">
              Erreur dans l&apos;onglet {this.props.tabName ?? "Analyse"}
            </p>
            <p className="text-slate-500 dark:text-slate-400 text-sm max-w-md">
              Une erreur inattendue s&apos;est produite lors du rendu de cet
              onglet. Les autres onglets restent accessibles.
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 px-4 py-2 min-h-[44px] bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <RotateCcw className="w-4 h-4" aria-hidden="true" />
            Réessayer
          </button>
          {process.env.NODE_ENV === "development" && this.state.error && (
            <pre className="mt-2 text-left text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg max-w-full overflow-auto">
              {this.state.error.message}
            </pre>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default TabErrorBoundary;
