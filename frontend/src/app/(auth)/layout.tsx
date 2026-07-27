import type { ReactNode } from "react";

import { BrandMark } from "@/components/brand-mark";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-surface p-8 shadow-2xl">
        <div className="mb-6 flex justify-center">
          <BrandMark />
        </div>
        {children}
      </div>
      <p className="text-xs text-slate-400">Powered by ChengetAi Labs</p>
    </div>
  );
}
