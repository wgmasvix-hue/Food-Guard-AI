"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Package, Plus, Search, Waypoints } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState, EmptyTableRow } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { BatchTraceResult, LotTraceResult, RawMaterialLot } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const LOT_STATUSES = ["active", "quarantined", "consumed", "rejected"] as const;

const LOT_STATUS_TONE: Record<string, "green" | "gray" | "red" | "amber"> = {
  active: "green",
  quarantined: "amber",
  consumed: "gray",
  rejected: "red",
};

const EMPTY_FORM = { material_name: "", lot_number: "", received_date: "", expiry_date: "", quantity_received: "", unit: "", notes: "" };

function TraceSearch() {
  const toast = useToast();
  const [mode, setMode] = useState<"lot" | "batch">("lot");
  const [query, setQuery] = useState("");
  const [lotResult, setLotResult] = useState<LotTraceResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchTraceResult | null>(null);
  const [searching, setSearching] = useState(false);
  const [notFound, setNotFound] = useState(false);

  async function runTrace(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setNotFound(false);
    setLotResult(null);
    setBatchResult(null);
    try {
      if (mode === "lot") {
        const { data } = await api.get<LotTraceResult>(`/traceability/trace/lot/${encodeURIComponent(query.trim())}`);
        setLotResult(data);
      } else {
        const { data } = await api.get<BatchTraceResult>(`/traceability/trace/batch/${encodeURIComponent(query.trim())}`);
        setBatchResult(data);
      }
    } catch (err) {
      setNotFound(true);
      toast.error(apiErrorMessage(err, "Not found"));
    } finally {
      setSearching(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Waypoints className="h-4 w-4" /> Recall Trace</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-sm text-ink-500">
          Trace a <strong>raw material lot</strong> forward to every finished batch it affected, or a{" "}
          <strong>finished batch</strong> backward to every raw material lot used in it.
        </p>
        <form onSubmit={runTrace} className="flex flex-col gap-2 sm:flex-row">
          <Select value={mode} onChange={(e) => setMode(e.target.value as "lot" | "batch")} className="w-full sm:w-48">
            <option value="lot">By raw material lot #</option>
            <option value="batch">By finished batch #</option>
          </Select>
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={mode === "lot" ? "e.g. L-2026-0142" : "e.g. B-2026-0087"}
              className="pl-9"
            />
          </div>
          <Button type="submit" disabled={searching}>{searching ? "Tracing…" : "Trace"}</Button>
        </form>

        {notFound && <p className="mt-4 text-sm text-ink-500">No {mode === "lot" ? "lot" : "batch"} found with that number.</p>}

        {lotResult && (
          <div className="mt-5 space-y-3">
            <div className="rounded-lg bg-ink-50 p-3 text-sm">
              <p className="font-medium text-ink-800">{lotResult.lot.material_name} — lot {lotResult.lot.lot_number}</p>
              <p className="mt-0.5 text-ink-500">
                Received {formatDate(lotResult.lot.received_date)} · Status: <StatusBadge status={lotResult.lot.status} />
              </p>
            </div>
            <p className="text-sm font-medium text-ink-700">
              {lotResult.affected_batches.length === 0
                ? "This lot hasn't been recorded as used in any batch."
                : `Affects ${lotResult.affected_batches.length} finished batch${lotResult.affected_batches.length === 1 ? "" : "es"}:`}
            </p>
            <ul className="space-y-2">
              {lotResult.affected_batches.map((b) => (
                <li key={b.id} className="flex items-center justify-between rounded-lg border border-ink-200 px-3 py-2 text-sm">
                  <span className="font-medium text-ink-800">Batch {b.batch_number}</span>
                  <StatusBadge status={b.status} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {batchResult && (
          <div className="mt-5 space-y-3">
            <div className="rounded-lg bg-ink-50 p-3 text-sm">
              <p className="font-medium text-ink-800">Batch {batchResult.batch.batch_number}</p>
              <p className="mt-0.5 text-ink-500">
                Produced {formatDate(batchResult.batch.production_date)} · Status: <StatusBadge status={batchResult.batch.status} />
              </p>
              {batchResult.batch.recall_reason && (
                <p className="mt-1 font-medium text-red-700">Recall reason: {batchResult.batch.recall_reason}</p>
              )}
            </div>
            <p className="text-sm font-medium text-ink-700">
              {batchResult.lots_used.length === 0
                ? "No raw material lots recorded for this batch."
                : `Used ${batchResult.lots_used.length} raw material lot${batchResult.lots_used.length === 1 ? "" : "s"}:`}
            </p>
            <ul className="space-y-2">
              {batchResult.lots_used.map((u) => (
                <li key={u.id} className="flex items-center justify-between rounded-lg border border-ink-200 px-3 py-2 text-sm">
                  <span className="font-medium text-ink-800">
                    {u.raw_material_lot.material_name} — lot {u.raw_material_lot.lot_number}
                  </span>
                  <span className="text-ink-500">{u.quantity_used ?? "—"} {u.unit ?? ""}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TraceabilityPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: lots, isLoading } = useQuery({
    queryKey: ["raw-material-lots"],
    queryFn: async () => (await api.get<RawMaterialLot[]>("/traceability/lots")).data,
  });

  async function createLot(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/traceability/lots", {
        ...form,
        received_date: form.received_date || null,
        expiry_date: form.expiry_date || null,
        quantity_received: form.quantity_received ? Number(form.quantity_received) : null,
      });
      await queryClient.invalidateQueries({ queryKey: ["raw-material-lots"] });
      setCreateOpen(false);
      setForm(EMPTY_FORM);
      toast.success("Raw material lot recorded.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  async function updateStatus(id: string, status: RawMaterialLot["status"]) {
    try {
      await api.patch(`/traceability/lots/${id}`, { status });
      await queryClient.invalidateQueries({ queryKey: ["raw-material-lots"] });
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="Traceability">
      <div className="space-y-6">
        <TraceSearch />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Package className="h-4 w-4" /> Raw Material Lots</CardTitle>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-3.5 w-3.5" /> Record Lot
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-16 z-10 bg-surface">
                  <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                    <th className="px-5 py-3">Material</th>
                    <th className="px-5 py-3">Lot #</th>
                    <th className="px-5 py-3">Received</th>
                    <th className="px-5 py-3">Quantity</th>
                    <th className="px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-100">
                  {isLoading && <TableSkeleton columns={5} />}
                  {lots?.map((lot) => (
                    <tr key={lot.id} className="transition-colors hover:bg-ink-50">
                      <td className="px-5 py-3 font-medium text-ink-800">{lot.material_name}</td>
                      <td className="px-5 py-3 font-mono text-xs text-ink-600">{lot.lot_number}</td>
                      <td className="px-5 py-3 text-ink-600">{formatDate(lot.received_date)}</td>
                      <td className="px-5 py-3 text-ink-600">{lot.quantity_received ?? "—"} {lot.unit ?? ""}</td>
                      <td className="px-5 py-3">
                        <Select
                          value={lot.status}
                          onChange={(e) => updateStatus(lot.id, e.target.value as RawMaterialLot["status"])}
                          className="h-8 w-auto text-xs"
                        >
                          {LOT_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                        </Select>
                      </td>
                    </tr>
                  ))}
                  {!isLoading && lots?.length === 0 && (
                    <EmptyTableRow
                      colSpan={5}
                      icon={Package}
                      title="No raw material lots recorded yet"
                      description="Record each incoming lot so it can be traced into whatever batches use it."
                    />
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Record Raw Material Lot">
        <form onSubmit={createLot} className="space-y-4">
          <div>
            <Label>Material name</Label>
            <Input required value={form.material_name} onChange={(e) => setForm({ ...form, material_name: e.target.value })} placeholder="Wheat Flour" />
          </div>
          <div>
            <Label>Lot number</Label>
            <Input required value={form.lot_number} onChange={(e) => setForm({ ...form, lot_number: e.target.value })} placeholder="L-2026-0142" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Received date</Label>
              <Input type="date" value={form.received_date} onChange={(e) => setForm({ ...form, received_date: e.target.value })} />
            </div>
            <div>
              <Label>Expiry date</Label>
              <Input type="date" value={form.expiry_date} onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Quantity received</Label>
              <Input type="number" step="any" value={form.quantity_received} onChange={(e) => setForm({ ...form, quantity_received: e.target.value })} />
            </div>
            <div>
              <Label>Unit</Label>
              <Input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} placeholder="kg" />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Recording…" : "Record Lot"}</Button>
          </div>
        </form>
      </Dialog>
    </ProtectedShell>
  );
}
