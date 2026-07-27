import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-ink-200/70", className)} />;
}

/** Placeholder rows for a <table> body while data is loading. */
export function TableSkeleton({ columns, rows = 5 }: { columns: number; rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r}>
          {Array.from({ length: columns }).map((__, c) => (
            <td key={c} className="px-5 py-3">
              <Skeleton className="h-4 w-full max-w-[16rem]" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

/** Placeholder grid of card-shaped tiles while data is loading. */
export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-xl border border-ink-200 bg-surface p-5 shadow-sm">
          <Skeleton className="mb-3 h-9 w-9 rounded-lg" />
          <Skeleton className="mb-2 h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

/** Placeholder for the dashboard's stat tiles + widget cards. */
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-ink-200 bg-surface p-6 md:col-span-1">
          <Skeleton className="mx-auto h-32 w-32 rounded-full" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 md:col-span-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 rounded-xl border border-ink-200 bg-surface p-5">
              <Skeleton className="h-11 w-11 shrink-0 rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-6 w-12" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-3 rounded-xl border border-ink-200 bg-surface p-5">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    </div>
  );
}
