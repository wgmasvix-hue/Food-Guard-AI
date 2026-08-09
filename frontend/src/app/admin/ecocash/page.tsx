"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";
import type { EcocashPayment } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

function formatPrice(cents: number, currency: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() }).format(cents / 100);
}

export default function EcocashAdminPage() {
  const { user } = useAuth();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const { data: pending, isLoading } = useQuery({
    queryKey: ["ecocash-pending"],
    queryFn: async () => (await api.get<EcocashPayment[]>("/billing/ecocash/pending")).data,
    enabled: user?.role === "super_admin",
  });

  async function approve(id: string) {
    setBusyId(id);
    try {
      await api.post(`/billing/ecocash/${id}/approve`);
      await queryClient.invalidateQueries({ queryKey: ["ecocash-pending"] });
      toast.success("Payment approved — plan activated.");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id: string) {
    setBusyId(id);
    try {
      await api.post(`/billing/ecocash/${id}/reject`, { reason: reason || undefined });
      await queryClient.invalidateQueries({ queryKey: ["ecocash-pending"] });
      toast.success("Payment rejected.");
      setRejecting(null);
      setReason("");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  if (user && user.role !== "super_admin") {
    return (
      <ProtectedShell title="EcoCash Payments">
        <Card><CardContent className="py-10 text-center text-sm text-ink-500">Super Admin access only.</CardContent></Card>
      </ProtectedShell>
    );
  }

  return (
    <ProtectedShell title="EcoCash Payments">
      <p className="mb-4 text-sm text-ink-500">
        Pending EcoCash payments awaiting manual review. Approving activates the plan on that company&apos;s subscription immediately.
      </p>

      {isLoading && <p className="text-sm text-ink-400">Loading…</p>}
      {pending?.length === 0 && (
        <Card>
          <CardContent className="p-0">
            <EmptyState icon={CheckCircle2} title="Nothing pending review" description="New EcoCash payment submissions will show up here for approval." />
          </CardContent>
        </Card>
      )}

      <div className="space-y-4">
        {pending?.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <CardTitle>
                {p.plan.name} — {formatPrice(p.amount_cents, p.currency)}
              </CardTitle>
              <span className="font-mono text-xs text-ink-400">{p.reference_code}</span>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                <div>
                  <p className="text-ink-400">Transaction ref</p>
                  <p className="font-mono font-medium text-ink-800">{p.transaction_reference}</p>
                </div>
                <div>
                  <p className="text-ink-400">Payer phone</p>
                  <p className="font-medium text-ink-800">{p.payer_phone ?? "—"}</p>
                </div>
                <div>
                  <p className="text-ink-400">Submitted</p>
                  <p className="font-medium text-ink-800">{formatDateTime(p.created_at)}</p>
                </div>
              </div>

              {rejecting === p.id ? (
                <div className="mt-4 space-y-2">
                  <Label>Rejection reason (optional)</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Reference not found" />
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setRejecting(null)}>Cancel</Button>
                    <Button size="sm" variant="destructive" disabled={busyId === p.id} onClick={() => reject(p.id)}>
                      {busyId === p.id ? "Rejecting…" : "Confirm Reject"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex gap-2">
                  <Button size="sm" disabled={busyId === p.id} onClick={() => approve(p.id)}>
                    {busyId === p.id ? "Approving…" : "Approve"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setRejecting(p.id)}>Reject</Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </ProtectedShell>
  );
}
