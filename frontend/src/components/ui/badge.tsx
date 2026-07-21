import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Tone = "green" | "gray" | "red" | "amber" | "blue";

const toneClasses: Record<Tone, string> = {
  green: "bg-brand-100 text-brand-800",
  gray: "bg-ink-100 text-ink-700",
  red: "bg-red-100 text-red-700",
  amber: "bg-amber-100 text-amber-800",
  blue: "bg-blue-100 text-blue-700",
};

export function Badge({
  className,
  tone = "gray",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

const STATUS_TONE: Record<string, Tone> = {
  open: "red",
  overdue: "red",
  failed: "red",
  in_progress: "amber",
  pending_verification: "amber",
  scheduled: "blue",
  draft: "gray",
  active: "green",
  approved: "green",
  closed: "green",
  completed: "green",
  cancelled: "gray",
  under_review: "amber",
  inactive: "gray",
};

export function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status] ?? "gray";
  return <Badge tone={tone}>{status.replace(/_/g, " ")}</Badge>;
}
