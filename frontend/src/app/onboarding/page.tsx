"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { OnboardingSetupResponse } from "@/lib/types";

const INDUSTRY_LABELS: Record<string, string> = {
  bakery: "Bakery",
  dairy: "Dairy",
  meat_poultry: "Meat & Poultry",
  seafood: "Seafood",
  beverages: "Beverages",
  fruits_vegetables: "Fruits & Vegetables",
  grain_milling: "Grain Milling",
  restaurant_food_service: "Restaurant / Food Service",
  catering: "Catering",
  confectionery: "Confectionery",
  other: "Other",
};

export default function OnboardingPage() {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [industry, setIndustry] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OnboardingSetupResponse | null>(null);

  const { data: industries } = useQuery({
    queryKey: ["onboarding-industries"],
    queryFn: async () => (await api.get<string[]>("/onboarding/industries")).data,
  });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const { data } = await api.post<OnboardingSetupResponse>("/onboarding/setup", {
        industry,
        process_description: description,
      });
      setResult(data);
      await queryClient.invalidateQueries({ queryKey: ["onboarding-status"] });
      await queryClient.invalidateQueries({ queryKey: ["haccp-plans"] });
      toast.success("Starter HACCP plan created.");
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (result) {
    return (
      <ProtectedShell title="Get Started">
        <Card className="mx-auto max-w-lg animate-fade-in-up">
          <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
              <CheckCircle2 className="h-7 w-7" />
            </span>
            <div>
              <p className="text-lg font-semibold text-ink-900">You&apos;re set up</p>
              <p className="mt-1 text-sm text-ink-500">{result.message}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push(`/haccp/${result.haccp_plan_id}`)}>
                Open HACCP Plan
              </Button>
              <Button onClick={() => router.push("/dashboard")}>Go to Dashboard</Button>
            </div>
          </CardContent>
        </Card>
      </ProtectedShell>
    );
  }

  return (
    <ProtectedShell title="Get Started">
      <Card className="mx-auto max-w-lg">
        <CardContent className="py-8">
          <div className="mb-6 flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <p className="font-semibold text-ink-900">Let&apos;s set up your first HACCP plan</p>
              <p className="text-sm text-ink-500">Tell us about your business — the AI Assistant drafts a starting point.</p>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label>Industry</Label>
              <Select required value={industry} onChange={(e) => setIndustry(e.target.value)}>
                <option value="">Select your industry…</option>
                {(industries ?? Object.keys(INDUSTRY_LABELS)).map((i) => (
                  <option key={i} value={i}>{INDUSTRY_LABELS[i] ?? i}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Describe your process</Label>
              <Textarea
                required
                minLength={10}
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. We bake bread loaves: mixing, proofing, baking, cooling, slicing, packaging, then chilled storage before delivery."
              />
              <p className="mt-1 text-xs text-ink-400">The more detail here, the more useful the AI-drafted starting point will be.</p>
            </div>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => router.push("/dashboard")}>Skip for now</Button>
              <Button type="submit" disabled={saving || !industry || description.length < 10}>
                {saving ? "Setting up…" : "Create Starter Plan"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </ProtectedShell>
  );
}
