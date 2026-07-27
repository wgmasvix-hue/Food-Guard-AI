import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { PwaRegister } from "@/components/pwa-register";
import { AuthProvider } from "@/lib/auth-context";
import { QueryProvider } from "@/lib/query-provider";
import { THEME_NO_FLASH_SCRIPT, ThemeProvider } from "@/lib/theme-context";
import { ToastProvider } from "@/lib/toast-context";

import "./globals.css";

export const metadata: Metadata = {
  title: "Food Guard AI",
  description: "AI-powered Food Safety, Quality Management, and Compliance System",
  manifest: "/manifest.json",
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/icon-192.png",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Food Guard AI",
  },
};

export const viewport: Viewport = {
  themeColor: "#16a34a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_NO_FLASH_SCRIPT }} />
      </head>
      <body>
        <PwaRegister />
        <ThemeProvider>
          <QueryProvider>
            <ToastProvider>
              <AuthProvider>{children}</AuthProvider>
            </ToastProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
