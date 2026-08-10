import { CheckCircle2, Smartphone } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/brand-mark";
import { ANDROID_APK_DOWNLOAD_URL } from "@/lib/constants";

const FEATURES = [
  "HACCP plans, GMP inspections & audits — all in one place",
  "AI assistant grounded in your own documents and live data",
  "Real-time compliance scoring across every facility",
  "Temperature monitoring with automatic out-of-range alerts",
];

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Hero panel — hidden below lg, always dark by design regardless of
          the app's light/dark theme (this is a fixed marketing surface,
          not app chrome, so it doesn't use the ink/surface tokens). */}
      <div className="relative hidden w-[44%] shrink-0 overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="animate-orb-drift absolute -left-24 -top-24 h-96 w-96 rounded-full bg-brand-500/20 blur-3xl" />
          <div
            className="animate-orb-drift absolute -bottom-32 -right-16 h-[28rem] w-[28rem] rounded-full bg-emerald-400/10 blur-3xl"
            style={{ animationDelay: "-9s" }}
          />
        </div>

        <div className="relative animate-fade-in-up">
          <BrandMark light />
        </div>

        <div className="relative animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          <h2 className="max-w-sm text-3xl font-semibold leading-tight tracking-tight text-white">
            Food safety, fully digitized.
          </h2>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-slate-300">
            One system for HACCP, GMP, audits, and compliance — built for teams who&apos;d rather prevent
            problems than paper over them.
          </p>
          <ul className="mt-8 space-y-3">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-start gap-2.5 text-sm text-slate-200">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-400" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        <div
          className="relative animate-fade-in-up flex items-center justify-between text-xs text-slate-400"
          style={{ animationDelay: "0.2s" }}
        >
          <span>Powered by ChengetAi Labs</span>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="hover:text-slate-200">
              Privacy
            </Link>
            <a href={ANDROID_APK_DOWNLOAD_URL} className="flex items-center gap-1.5 hover:text-slate-200">
              <Smartphone className="h-3.5 w-3.5" />
              Android App
            </a>
          </div>
        </div>
      </div>

      {/* Form panel — respects the app's light/dark theme tokens. */}
      <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-ink-50 px-4 py-10">
        <div className="lg:hidden">
          <BrandMark />
        </div>

        <div className="w-full max-w-md animate-fade-in-up rounded-3xl border border-ink-200/70 bg-surface p-8 shadow-soft-lg">
          {children}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-ink-400">
          <a href={ANDROID_APK_DOWNLOAD_URL} className="flex items-center gap-1.5 hover:text-ink-600 lg:hidden">
            <Smartphone className="h-3.5 w-3.5" />
            Download Android App
          </a>
          <Link href="/privacy" className="hover:text-ink-600">
            Privacy Policy
          </Link>
          <span className="lg:hidden">Powered by ChengetAi Labs</span>
        </div>
      </div>
    </div>
  );
}
