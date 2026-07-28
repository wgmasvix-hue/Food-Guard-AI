import { Smartphone } from "lucide-react";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/brand-mark";
import { ANDROID_APK_DOWNLOAD_URL } from "@/lib/constants";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-surface p-8 shadow-2xl">
        <div className="mb-6 flex justify-center">
          <BrandMark />
        </div>
        {children}
      </div>
      <a
        href={ANDROID_APK_DOWNLOAD_URL}
        className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white"
      >
        <Smartphone className="h-3.5 w-3.5" />
        Download Android App
      </a>
      <p className="text-xs text-slate-400">Powered by ChengetAi Labs</p>
    </div>
  );
}
