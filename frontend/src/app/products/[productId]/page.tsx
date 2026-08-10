"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Boxes, Plus, Trash2 } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState, EmptyTableRow } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { Batch, BatchLotUsage, FormulationItem, Product, ProductFormulation, RawMaterialLot } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const BATCH_STATUSES = ["in_production", "released", "on_hold", "recalled"] as const;

type DraftItem = {
  name: string;
  percentage: string;
  quantity: string;
  unit: string;
  unit_cost: string;
  is_allergen: boolean;
};

const EMPTY_ITEM: DraftItem = { name: "", percentage: "", quantity: "", unit: "", unit_cost: "", is_allergen: false };

export default function ProductDetailPage() {
  const params = useParams<{ productId: string }>();
  const productId = params.productId;
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: product } = useQuery({
    queryKey: ["product", productId],
    queryFn: async () => (await api.get<Product>(`/products/${productId}`)).data,
  });
  const { data: formulations } = useQuery({
    queryKey: ["formulations", productId],
    queryFn: async () => (await api.get<ProductFormulation[]>(`/products/${productId}/formulations`)).data,
  });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = formulations?.find((f) => f.id === selectedId) ?? formulations?.[0] ?? null;

  const [createOpen, setCreateOpen] = useState(false);
  const [batchSize, setBatchSize] = useState("");
  const [batchUnit, setBatchUnit] = useState("kg");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<DraftItem[]>([{ ...EMPTY_ITEM }]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function updateItem(index: number, patch: Partial<DraftItem>) {
    setItems((current) => current.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  async function createFormulation(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post(`/products/${productId}/formulations`, {
        batch_size: batchSize ? Number(batchSize) : null,
        batch_size_unit: batchUnit || null,
        notes: notes || null,
        items: items
          .filter((item) => item.name.trim())
          .map((item) => ({
            name: item.name,
            percentage: item.percentage ? Number(item.percentage) : null,
            quantity: item.quantity ? Number(item.quantity) : null,
            unit: item.unit || null,
            unit_cost: item.unit_cost ? Number(item.unit_cost) : null,
            is_allergen: item.is_allergen,
          })),
      });
      await queryClient.invalidateQueries({ queryKey: ["formulations", productId] });
      setCreateOpen(false);
      setBatchSize("");
      setNotes("");
      setItems([{ ...EMPTY_ITEM }]);
      toast.success("New formulation version created.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  async function setActive(formulationId: string) {
    try {
      await api.patch(`/products/${productId}/formulations/${formulationId}`, { status: "active" });
      await queryClient.invalidateQueries({ queryKey: ["formulations", productId] });
      toast.success("Formulation set as active.");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title={product?.name ?? "Product"}>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Versions</CardTitle>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-3.5 w-3.5" /> New Version
            </Button>
          </CardHeader>
          <CardContent className="space-y-2">
            {formulations?.length === 0 && (
              <EmptyState title="No formulations yet" className="py-6" />
            )}
            {formulations?.map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedId(f.id)}
                className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm transition-colors ${
                  selected?.id === f.id ? "border-brand-500 bg-brand-50" : "border-ink-200/70 hover:bg-ink-50"
                }`}
              >
                <span className="font-medium text-ink-800">Version {f.version}</span>
                <StatusBadge status={f.status} />
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{selected ? `Version ${selected.version} details` : "Select a version"}</CardTitle>
            {selected && selected.status === "draft" && (
              <Button size="sm" variant="outline" onClick={() => setActive(selected.id)}>
                Set as Active
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {!selected ? (
              <p className="py-10 text-center text-sm text-ink-400">
                Create a formulation version to define this product&apos;s ingredient composition.
              </p>
            ) : (
              <>
                <div className="mb-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-ink-400">Batch size</p>
                    <p className="font-medium text-ink-800">
                      {selected.batch_size ? `${selected.batch_size} ${selected.batch_size_unit ?? ""}` : "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-ink-400">Total composition</p>
                    <p className={`font-medium ${Math.round(selected.total_percentage) === 100 ? "text-ink-800" : "text-amber-700"}`}>
                      {selected.total_percentage.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-ink-400">Est. cost / batch</p>
                    <p className="font-medium text-ink-800">${selected.total_cost.toFixed(2)}</p>
                  </div>
                </div>
                {selected.allergens.length > 0 && (
                  <p className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
                    Allergens: {selected.allergens.join(", ")}
                  </p>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                        <th className="py-2 pr-3">Ingredient</th>
                        <th className="py-2 pr-3">%</th>
                        <th className="py-2 pr-3">Qty</th>
                        <th className="py-2 pr-3">Unit cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-100">
                      {selected.items.map((item: FormulationItem) => (
                        <tr key={item.id}>
                          <td className="py-2 pr-3 font-medium text-ink-800">
                            {item.name} {item.is_allergen && <span className="text-amber-600">⚠</span>}
                          </td>
                          <td className="py-2 pr-3 text-ink-600">{item.percentage ?? "—"}</td>
                          <td className="py-2 pr-3 text-ink-600">
                            {item.quantity ?? "—"} {item.unit ?? ""}
                          </td>
                          <td className="py-2 pr-3 text-ink-600">{item.unit_cost ? `$${item.unit_cost}` : "—"}</td>
                        </tr>
                      ))}
                      {selected.items.length === 0 && (
                        <EmptyTableRow colSpan={4} title="No ingredients added yet" description="Add each ingredient's percentage, quantity, and cost below." />
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New Formulation Version"
        description="Define the ingredient composition for this version."
        className="max-w-2xl"
      >
        <form onSubmit={createFormulation} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Batch size</Label>
              <Input type="number" step="any" value={batchSize} onChange={(e) => setBatchSize(e.target.value)} placeholder="e.g. 100" />
            </div>
            <div>
              <Label>Unit</Label>
              <Input value={batchUnit} onChange={(e) => setBatchUnit(e.target.value)} placeholder="kg" />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
          </div>

          <div>
            <Label>Ingredients</Label>
            <div className="space-y-2">
              {items.map((item, i) => (
                <div key={i} className="grid grid-cols-12 items-center gap-2 rounded-xl border border-ink-200/70 p-2">
                  <Input
                    className="col-span-4"
                    placeholder="Ingredient name"
                    value={item.name}
                    onChange={(e) => updateItem(i, { name: e.target.value })}
                  />
                  <Input
                    className="col-span-2"
                    type="number"
                    step="any"
                    placeholder="%"
                    value={item.percentage}
                    onChange={(e) => updateItem(i, { percentage: e.target.value })}
                  />
                  <Input
                    className="col-span-2"
                    type="number"
                    step="any"
                    placeholder="Qty"
                    value={item.quantity}
                    onChange={(e) => updateItem(i, { quantity: e.target.value })}
                  />
                  <Input
                    className="col-span-2"
                    type="number"
                    step="any"
                    placeholder="Cost/unit"
                    value={item.unit_cost}
                    onChange={(e) => updateItem(i, { unit_cost: e.target.value })}
                  />
                  <label className="col-span-1 flex items-center justify-center" title="Allergen">
                    <input
                      type="checkbox"
                      checked={item.is_allergen}
                      onChange={(e) => updateItem(i, { is_allergen: e.target.checked })}
                    />
                  </label>
                  <button
                    type="button"
                    className="col-span-1 flex items-center justify-center text-ink-400 hover:text-red-600"
                    onClick={() => setItems((current) => current.filter((_, idx) => idx !== i))}
                    aria-label="Remove ingredient"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => setItems((current) => [...current, { ...EMPTY_ITEM }])}
            >
              <Plus className="h-3.5 w-3.5" /> Add Ingredient
            </Button>
          </div>

          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save Version"}</Button>
          </div>
        </form>
      </Dialog>

      <BatchesSection productId={productId} />
    </ProtectedShell>
  );
}

function BatchesSection({ productId }: { productId: string }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: batches } = useQuery({
    queryKey: ["batches", productId],
    queryFn: async () => (await api.get<Batch[]>(`/products/${productId}/batches`)).data,
  });
  const { data: lots } = useQuery({
    queryKey: ["raw-material-lots"],
    queryFn: async () => (await api.get<RawMaterialLot[]>("/traceability/lots")).data,
  });

  const [createOpen, setCreateOpen] = useState(false);
  const [batchForm, setBatchForm] = useState({ batch_number: "", quantity: "", unit: "", production_date: "", expiry_date: "" });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [selected, setSelected] = useState<Batch | null>(null);
  const [pendingStatus, setPendingStatus] = useState<string>("in_production");
  const [recallReason, setRecallReason] = useState("");
  const [statusError, setStatusError] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [addLotId, setAddLotId] = useState("");
  const [addLotQty, setAddLotQty] = useState("");

  const { data: usages, refetch: refetchUsages } = useQuery({
    queryKey: ["batch-lots", selected?.id],
    queryFn: async () => (await api.get<BatchLotUsage[]>(`/products/${productId}/batches/${selected!.id}/lots`)).data,
    enabled: !!selected,
  });

  async function createBatch(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post(`/products/${productId}/batches`, {
        product_id: productId,
        batch_number: batchForm.batch_number,
        quantity: batchForm.quantity ? Number(batchForm.quantity) : null,
        unit: batchForm.unit || null,
        production_date: batchForm.production_date || null,
        expiry_date: batchForm.expiry_date || null,
      });
      await queryClient.invalidateQueries({ queryKey: ["batches", productId] });
      setCreateOpen(false);
      setBatchForm({ batch_number: "", quantity: "", unit: "", production_date: "", expiry_date: "" });
      toast.success("Batch recorded.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  }

  async function saveStatus(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setStatusError(null);
    setUpdatingStatus(true);
    try {
      const { data } = await api.patch<Batch>(`/products/${productId}/batches/${selected.id}`, {
        status: pendingStatus,
        recall_reason: recallReason || undefined,
      });
      queryClient.setQueryData<Batch[]>(["batches", productId], (prev) => prev?.map((b) => (b.id === data.id ? data : b)));
      setSelected(data);
      toast.success(pendingStatus === "recalled" ? "Batch marked as recalled." : "Batch status updated.");
    } catch (err) {
      setStatusError(apiErrorMessage(err));
    } finally {
      setUpdatingStatus(false);
    }
  }

  async function addLotUsage(e: React.FormEvent) {
    e.preventDefault();
    if (!selected || !addLotId) return;
    try {
      await api.post(`/products/${productId}/batches/${selected.id}/lots`, {
        raw_material_lot_id: addLotId,
        quantity_used: addLotQty ? Number(addLotQty) : null,
      });
      setAddLotId("");
      setAddLotQty("");
      await refetchUsages();
      toast.success("Lot linked to batch.");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  }

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Boxes className="h-4 w-4" /> Production Batches</CardTitle>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="h-3.5 w-3.5" /> New Batch
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                <th className="px-5 py-3">Batch #</th>
                <th className="px-5 py-3">Produced</th>
                <th className="px-5 py-3">Quantity</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {batches?.map((b) => (
                <tr
                  key={b.id}
                  className="cursor-pointer transition-colors hover:bg-ink-50"
                  onClick={() => {
                    setSelected(b);
                    setPendingStatus(b.status);
                    setRecallReason(b.recall_reason ?? "");
                    setStatusError(null);
                  }}
                >
                  <td className="px-5 py-3 font-mono text-xs font-medium text-ink-800">{b.batch_number}</td>
                  <td className="px-5 py-3 text-ink-600">{formatDate(b.production_date)}</td>
                  <td className="px-5 py-3 text-ink-600">{b.quantity ?? "—"} {b.unit ?? ""}</td>
                  <td className="px-5 py-3"><StatusBadge status={b.status} /></td>
                </tr>
              ))}
              {batches?.length === 0 && (
                <EmptyTableRow
                  colSpan={4}
                  icon={Boxes}
                  title="No batches recorded yet"
                  description="Record a production batch to start tracing which raw material lots went into it."
                />
              )}
            </tbody>
          </table>
        </div>
      </CardContent>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="New Production Batch">
        <form onSubmit={createBatch} className="space-y-4">
          <div>
            <Label>Batch number</Label>
            <Input required value={batchForm.batch_number} onChange={(e) => setBatchForm({ ...batchForm, batch_number: e.target.value })} placeholder="B-2026-0087" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Quantity</Label>
              <Input type="number" step="any" value={batchForm.quantity} onChange={(e) => setBatchForm({ ...batchForm, quantity: e.target.value })} />
            </div>
            <div>
              <Label>Unit</Label>
              <Input value={batchForm.unit} onChange={(e) => setBatchForm({ ...batchForm, unit: e.target.value })} placeholder="kg" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Production date</Label>
              <Input type="date" value={batchForm.production_date} onChange={(e) => setBatchForm({ ...batchForm, production_date: e.target.value })} />
            </div>
            <div>
              <Label>Expiry date</Label>
              <Input type="date" value={batchForm.expiry_date} onChange={(e) => setBatchForm({ ...batchForm, expiry_date: e.target.value })} />
            </div>
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save Batch"}</Button>
          </div>
        </form>
      </Dialog>

      {selected && (
        <Dialog open onClose={() => setSelected(null)} title={`Batch ${selected.batch_number}`} className="max-w-lg">
          <div className="space-y-4">
            <form onSubmit={saveStatus} className="space-y-3">
              <div>
                <Label>Status</Label>
                <Select value={pendingStatus} onChange={(e) => setPendingStatus(e.target.value)}>
                  {BATCH_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
                </Select>
              </div>
              {pendingStatus === "recalled" && (
                <div>
                  <Label>Recall reason <span className="text-red-600">*</span></Label>
                  <Textarea
                    value={recallReason}
                    onChange={(e) => setRecallReason(e.target.value)}
                    placeholder="Why is this batch being recalled?"
                    rows={2}
                  />
                </div>
              )}
              {statusError && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{statusError}</p>}
              {(pendingStatus !== selected.status || (pendingStatus === "recalled" && recallReason !== (selected.recall_reason ?? ""))) && (
                <div className="flex justify-end">
                  <Button type="submit" size="sm" disabled={updatingStatus}>
                    {updatingStatus ? "Saving…" : "Update Status"}
                  </Button>
                </div>
              )}
            </form>

            <div className="border-t border-ink-100 pt-4">
              <Label>Raw material lots used</Label>
              <ul className="mt-2 space-y-2">
                {usages?.map((u) => (
                  <li key={u.id} className="flex items-center justify-between rounded-lg border border-ink-200 px-3 py-2 text-sm">
                    <span className="font-medium text-ink-800">{u.raw_material_lot.material_name} — {u.raw_material_lot.lot_number}</span>
                    <span className="text-ink-500">{u.quantity_used ?? "—"} {u.unit ?? ""}</span>
                  </li>
                ))}
                {usages?.length === 0 && <p className="text-sm text-ink-400">No lots linked yet.</p>}
              </ul>
              <form onSubmit={addLotUsage} className="mt-3 flex items-end gap-2">
                <div className="flex-1">
                  <Label>Add lot</Label>
                  <Select value={addLotId} onChange={(e) => setAddLotId(e.target.value)}>
                    <option value="">Select a lot…</option>
                    {lots?.map((l) => <option key={l.id} value={l.id}>{l.material_name} — {l.lot_number}</option>)}
                  </Select>
                </div>
                <div className="w-28">
                  <Label>Qty used</Label>
                  <Input type="number" step="any" value={addLotQty} onChange={(e) => setAddLotQty(e.target.value)} />
                </div>
                <Button type="submit" size="sm" disabled={!addLotId}>Add</Button>
              </form>
            </div>
          </div>
        </Dialog>
      )}
    </Card>
  );
}
