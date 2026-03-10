"use client";

function Pulse({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse bg-slate-200 rounded ${className}`} />;
}

export function AnalysisTabSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Pulse className="h-6 w-48" />
        <Pulse className="h-5 w-20 rounded-full" />
      </div>
      {/* Score bar */}
      <Pulse className="h-3 w-full max-w-md rounded-full" />
      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="border border-slate-200 rounded-lg p-4 space-y-3">
            <Pulse className="h-4 w-32" />
            <Pulse className="h-3 w-full" />
            <Pulse className="h-3 w-3/4" />
            <div className="flex gap-2 pt-1">
              <Pulse className="h-5 w-16 rounded-full" />
              <Pulse className="h-5 w-12 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SummaryTabSkeleton() {
  return (
    <div className="space-y-4 animate-fade-in">
      <Pulse className="h-6 w-64" />
      <Pulse className="h-4 w-full" />
      <Pulse className="h-4 w-5/6" />
      <Pulse className="h-4 w-4/5" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-slate-50 rounded-lg p-4 space-y-2">
            <Pulse className="h-8 w-16" />
            <Pulse className="h-3 w-24" />
          </div>
        ))}
      </div>
      <div className="space-y-2 mt-6">
        {[1, 2, 3, 4, 5].map(i => (
          <Pulse key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}

export function ChecklistTabSkeleton() {
  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center gap-3 mb-4">
        <Pulse className="h-6 w-40" />
        <Pulse className="h-8 w-24 rounded-lg" />
        <Pulse className="h-8 w-24 rounded-lg" />
      </div>
      {[1, 2, 3, 4, 5, 6].map(i => (
        <div key={i} className="border border-slate-200 rounded-lg p-4 flex items-start gap-3">
          <Pulse className="h-5 w-5 rounded flex-shrink-0 mt-0.5" />
          <div className="flex-1 space-y-2">
            <Pulse className="h-4 w-3/4" />
            <Pulse className="h-3 w-full" />
            <div className="flex gap-2">
              <Pulse className="h-5 w-16 rounded-full" />
              <Pulse className="h-5 w-20 rounded-full" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
