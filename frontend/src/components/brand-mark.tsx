import { ShieldCheck } from "lucide-react";

export function BrandMark({ className }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className ?? ""}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
        <ShieldCheck className="h-5 w-5" />
      </span>
      <span className="text-lg font-semibold tracking-tight text-ink-900">
        Food Guard <span className="text-brand-600">AI</span>
      </span>
    </div>
  );
}
