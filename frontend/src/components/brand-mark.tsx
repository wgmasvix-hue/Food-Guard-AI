import { ShieldCheck } from "lucide-react";

/** `light` renders the wordmark for placement on a dark/gradient
 * background (e.g. the auth hero panel) instead of the app surface. */
export function BrandMark({ className, light = false }: { className?: string; light?: boolean }) {
  return (
    <div className={`flex items-center gap-2 ${className ?? ""}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-soft">
        <ShieldCheck className="h-5 w-5" />
      </span>
      <span className={`text-lg font-semibold tracking-tight ${light ? "text-white" : "text-ink-900"}`}>
        Food<span className={light ? "text-brand-300" : "text-brand-600"}>OS</span>
      </span>
    </div>
  );
}
