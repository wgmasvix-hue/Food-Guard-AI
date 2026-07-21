"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { tokenStore } from "@/lib/api-client";

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace(tokenStore.getAccess() ? "/dashboard" : "/login");
  }, [router]);

  return null;
}
