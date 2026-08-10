"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Truck } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyTableRow } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { Supplier } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const APPROVAL_STATUSES = ["pending", "approved", "rejected", "suspended"] as const;
const RISK_RATINGS = ["low", "medium", "high"] as const;

const APPROVAL_TONE: Record<string, "green" | "gray" | "red" | "amber"> = {
  approved: "green",
  pending: "amber",
  rejected: "red",
  suspended: "red",
};

const EMPTY_FORM = { name: "", contact_name: "", email: "", phone: "", address: "", certification: "", certification_expires_on: "", risk_rating: "", notes: "" };

export default function SuppliersPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Supplier | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: suppliers, isLoading } = useQuery({
    queryKey: ["suppliers"],
    queryFn: async () => (await api.get<Supplier[]>("/products/suppliers/all")).data,
  });

  async function createSupplier(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/products/suppliers/all", {
        ...form,
        certification_expires_on: form.certification_expires_on || null,
        risk_rating: form.risk_rating || null,
      });
      await queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setCreateOpen(false);
      setForm(EMPTY_FORM);
      toast.success("Supplier added.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  async function updateSupplier(id: string, patch: Partial<Supplier>) {
    try {
      const { data } = await api.patch<Supplier>(`/products/suppliers/all/${id}`, patch);
      queryClient.setQueryData<Supplier[]>(["suppliers"], (prev) => prev?.map((s) => (s.id === id ? data : s)));
      setSelected(data);
      toast.success("Supplier updated.");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="Suppliers">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-500">Approved supplier list, certifications, and risk ratings.</p>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> New Supplier
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-16 z-10 bg-surface">
                <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Contact</th>
                  <th className="px-5 py-3">Certification</th>
                  <th className="px-5 py-3">Risk</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {isLoading && <TableSkeleton columns={5} />}
                {suppliers?.map((s) => (
                  <tr
                    key={s.id}
                    className="cursor-pointer transition-colors hover:bg-ink-50"
                    onClick={() => setSelected(s)}
                  >
                    <td className="px-5 py-3 font-medium text-ink-800">
                      {s.name}
                      {!s.is_active && <span className="ml-2 text-xs text-ink-400">(inactive)</span>}
                    </td>
                    <td className="px-5 py-3 text-ink-600">{s.contact_name || s.email || "—"}</td>
                    <td className="px-5 py-3 text-ink-600">
                      {s.certification || "—"}
                      {s.certification_expires_on && (
                        <span className="ml-1 text-xs text-ink-400">(exp. {formatDate(s.certification_expires_on)})</span>
                      )}
                    </td>
                    <td className="px-5 py-3 capitalize text-ink-600">{s.risk_rating || "—"}</td>
                    <td className="px-5 py-3">
                      <Badge tone={APPROVAL_TONE[s.approval_status] ?? "gray"}>{s.approval_status}</Badge>
                    </td>
                  </tr>
                ))}
                {!isLoading && suppliers?.length === 0 && (
                  <EmptyTableRow
                    colSpan={5}
                    icon={Truck}
                    title="No suppliers yet"
                    description="Add your raw material and packaging suppliers to track approval status and certifications."
                  />
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="New Supplier">
        <form onSubmit={createSupplier} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Flour Co Ltd" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Contact name</Label>
              <Input value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} />
            </div>
            <div>
              <Label>Email</Label>
              <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Phone</Label>
              <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div>
              <Label>Risk rating</Label>
              <Select value={form.risk_rating} onChange={(e) => setForm({ ...form, risk_rating: e.target.value })}>
                <option value="">Not assessed</option>
                {RISK_RATINGS.map((r) => <option key={r} value={r}>{r}</option>)}
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Certification</Label>
              <Input value={form.certification} onChange={(e) => setForm({ ...form, certification: e.target.value })} placeholder="e.g. BRC, FSSC 22000" />
            </div>
            <div>
              <Label>Certification expires</Label>
              <Input type="date" value={form.certification_expires_on} onChange={(e) => setForm({ ...form, certification_expires_on: e.target.value })} />
            </div>
          </div>
          <div>
            <Label>Address</Label>
            <Textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Adding…" : "Add Supplier"}</Button>
          </div>
        </form>
      </Dialog>

      {selected && (
        <Dialog open onClose={() => setSelected(null)} title={selected.name} description="Review and update approval status.">
          <div className="space-y-4">
            <div>
              <Label>Approval status</Label>
              <Select
                value={selected.approval_status}
                onChange={(e) => updateSupplier(selected.id, { approval_status: e.target.value as Supplier["approval_status"] })}
              >
                {APPROVAL_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
            <div>
              <Label>Risk rating</Label>
              <Select
                value={selected.risk_rating ?? ""}
                onChange={(e) => updateSupplier(selected.id, { risk_rating: (e.target.value || null) as Supplier["risk_rating"] })}
              >
                <option value="">Not assessed</option>
                {RISK_RATINGS.map((r) => <option key={r} value={r}>{r}</option>)}
              </Select>
            </div>
            <div className="rounded-lg bg-ink-50 p-3 text-sm text-ink-600">
              <p>{selected.contact_name}{selected.contact_name && selected.email ? " · " : ""}{selected.email}</p>
              {selected.phone && <p className="mt-1">{selected.phone}</p>}
              {selected.certification && (
                <p className="mt-1">
                  {selected.certification}
                  {selected.certification_expires_on && ` — expires ${formatDate(selected.certification_expires_on)}`}
                </p>
              )}
              {selected.notes && <p className="mt-2 whitespace-pre-wrap text-ink-500">{selected.notes}</p>}
            </div>
            <div className="flex justify-end">
              <Button
                variant={selected.is_active ? "destructive" : "outline"}
                size="sm"
                onClick={() => updateSupplier(selected.id, { is_active: !selected.is_active })}
              >
                {selected.is_active ? "Deactivate" : "Reactivate"}
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </ProtectedShell>
  );
}
