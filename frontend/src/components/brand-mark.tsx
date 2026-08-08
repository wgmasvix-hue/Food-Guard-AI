import { ShieldCheck } from "lucide-react";

export function BrandMark({ className }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className ?? ""}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-soft">
        <ShieldCheck className="h-5 w-5" />
      </span>
      <span className="text-lg font-semibold tracking-tight text-ink-900">
        Food<span className="text-brand-600">OS</span>
      </span>
    </div>
  );
}
