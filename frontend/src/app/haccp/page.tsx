"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusBadge } from "@/components/ui/badge";
import { CardGridSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { HaccpPlan } from "@/lib/types";

export default function HaccpPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", scope: "", process_description: "" });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: plans, isLoading } = useQuery({
    queryKey: ["haccp-plans"],
    queryFn: async () => (await api.get<HaccpPlan[]>("/haccp/plans")).data,
  });

  async function createPlan(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/haccp/plans", form);
      await queryClient.invalidateQueries({ queryKey: ["haccp-plans"] });
      setOpen(false);
      setForm({ name: "", scope: "", process_description: "" });
      toast.success("HACCP plan created.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedShell title="HACCP Plans">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-500">Hazard analysis, critical control points, and monitoring records.</p>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> New HACCP Plan
        </Button>
      </div>

      {isLoading ? (
        <CardGridSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {plans?.length === 0 && (
            <Card className="sm:col-span-2 lg:col-span-3">
              <CardContent className="py-10 text-center text-sm text-ink-500">
                No HACCP plans yet. Create your first plan or ask the AI Assistant to draft one.
              </CardContent>
            </Card>
          )}
          {plans?.map((plan) => (
            <Link key={plan.id} href={`/haccp/${plan.id}`}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardContent>
                  <div className="mb-2 flex items-start justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                      <ShieldAlert className="h-4 w-4" />
                    </span>
                    <StatusBadge status={plan.status} />
                  </div>
                  <p className="font-medium text-ink-900">{plan.name}</p>
                  <p className="mt-1 line-clamp-2 text-sm text-ink-500">{plan.scope || "No scope defined yet."}</p>
                  <p className="mt-3 text-xs text-ink-400">Version {plan.version}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} title="New HACCP Plan" description="Define the scope and process for hazard analysis.">
        <form onSubmit={createPlan} className="space-y-4">
          <div>
            <Label htmlFor="name">Plan name</Label>
            <Input id="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Peanut Butter Cookies HACCP Plan" />
          </div>
          <div>
            <Label htmlFor="scope">Scope</Label>
            <Textarea id="scope" value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })} placeholder="Product, facility, and process boundaries" />
          </div>
          <div>
            <Label htmlFor="process_description">Process description</Label>
            <Textarea id="process_description" value={form.process_description} onChange={(e) => setForm({ ...form, process_description: e.target.value })} placeholder="e.g. Mixing -> Baking -> Cooling -> Packaging" />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Create Plan"}</Button>
          </div>
        </form>
      </Dialog>
    </ProtectedShell>
  );
}
