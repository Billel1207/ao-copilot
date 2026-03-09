"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

/** Bloc skeleton de base avec animation shimmer */
export function Skeleton({ className }: SkeletonProps) {
  return <div className={cn("skeleton", className)} />;
}

/** Skeleton d'une stat card (dashboard) */
export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-5 shadow-card">
      <div className="flex items-start justify-between mb-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-7 w-16" />
        </div>
        <Skeleton className="h-10 w-10 rounded-xl" />
      </div>
      <Skeleton className="h-3 w-24" />
    </div>
  );
}

/** Skeleton d'une project card */
export function CardSkeleton() {
  return (
    <div className="card p-5 animate-slide-up">
      <div className="flex items-start justify-between mb-3">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full ml-3" />
      </div>
      <div className="flex gap-2 mt-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

/** Skeleton d'un tableau (checklist, etc.) */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-0 divide-y divide-slate-100">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 bg-slate-50 rounded-t-xl">
        <Skeleton className="h-3.5 w-32" />
        <Skeleton className="h-3.5 w-24 ml-auto" />
        <Skeleton className="h-3.5 w-20" />
        <Skeleton className="h-3.5 w-16" />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-4 py-3.5 items-center">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-5 w-20 rounded-full ml-auto" />
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton de la page de détail d'un projet */
export function ProjectDetailSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-7 w-80" />
        <Skeleton className="h-5 w-48" />
      </div>
      {/* Tabs */}
      <div className="flex gap-6 border-b border-slate-200 pb-0">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-5 w-20 mb-3" />
        ))}
      </div>
      {/* Content */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => <StatCardSkeleton key={i} />)}
      </div>
      <TableSkeleton rows={4} />
    </div>
  );
}

/** Skeleton de la liste de projets (dashboard) */
export function ProjectListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
