"use client";

import { useEffect } from "react";

/** Registers the service worker. Client component so it only runs in the
 * browser; failures are swallowed since the app must work fine without it. */
export function PwaRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {
        // Non-fatal: the app works fully without a service worker.
      });
    }
  }, []);

  return null;
}
