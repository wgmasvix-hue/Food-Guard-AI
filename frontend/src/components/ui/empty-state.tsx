import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

/** Consistent "nothing here yet" treatment — a subtle icon badge, a title,
 * an optional hint, and an optional call-to-action. Used in place of bare
 * gray text so every empty list in the app reads the same way. */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-1 px-6 py-10 text-center", className)}>
      {Icon && (
        <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-ink-100 text-ink-400">
          <Icon className="h-5 w-5" />
        </span>
      )}
      <p className="text-sm font-medium text-ink-700">{title}</p>
      {description && <p className="mt-0.5 max-w-sm text-sm text-ink-400">{description}</p>}
      {action && (
        <Button size="sm" variant="outline" className="mt-4" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

/** Same visual language as EmptyState, but as a single <tr> that spans a
 * table's columns — drop straight into a <tbody> in place of a map(). */
export function EmptyTableRow({
  colSpan,
  title,
  description,
  icon,
}: {
  colSpan: number;
  title: string;
  description?: string;
  icon?: LucideIcon;
}) {
  return (
    <tr>
      <td colSpan={colSpan} className="p-0">
        <EmptyState icon={icon} title={title} description={description} className="py-8" />
      </td>
    </tr>
  );
}
