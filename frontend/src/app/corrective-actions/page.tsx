"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { CorrectiveAction } from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/utils";

const STATUS_OPTIONS = ["open", "in_progress", "pending_verification", "closed", "overdue"];

export default function CorrectiveActionsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<CorrectiveAction | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: "", issue_description: "", root_cause: "", corrective_action: "", preventive_action: "", deadline: "",
  });

  const { data: cas, isLoading } = useQuery({
    queryKey: ["corrective-actions", statusFilter],
    queryFn: async () =>
      (
        await api.get<CorrectiveAction[]>("/corrective-actions", {
          params: statusFilter ? { status_filter: statusFilter } : undefined,
        })
      ).data,
  });

  async function createCa(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/corrective-actions", { ...form, deadline: form.deadline || null });
      await queryClient.invalidateQueries({ queryKey: ["corrective-actions"] });
      setCreateOpen(false);
      setForm({ title: "", issue_description: "", root_cause: "", corrective_action: "", preventive_action: "", deadline: "" });
      toast.success("Corrective action created.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  return (
    <ProtectedShell title="Corrective Actions">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink-500">Issue → root cause → corrective/preventive action → verification.</p>
        <div className="flex items-center gap-2">
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-auto">
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </Select>
          <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New Corrective Action</Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                  <th className="px-5 py-3">Title</th>
                  <th className="px-5 py-3">Source</th>
                  <th className="px-5 py-3">Deadline</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {isLoading && <TableSkeleton columns={4} />}
                {cas?.map((ca) => (
                  <tr key={ca.id} className="cursor-pointer hover:bg-ink-50" onClick={() => setSelected(ca)}>
                    <td className="px-5 py-3 font-medium text-ink-800">{ca.title}</td>
                    <td className="px-5 py-3 capitalize text-ink-600">{ca.source ?? "manual"}</td>
                    <td className="px-5 py-3 text-ink-600">{formatDate(ca.deadline)}</td>
                    <td className="px-5 py-3"><StatusBadge status={ca.status} /></td>
                  </tr>
                ))}
                {cas?.length === 0 && (
                  <tr><td colSpan={4} className="py-6 text-center text-ink-400">
                    {statusFilter ? `No corrective actions with status "${statusFilter.replace(/_/g, " ")}".` : "No corrective actions yet."}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="New Corrective Action">
        <form onSubmit={createCa} className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <Label>Issue description</Label>
            <Textarea required value={form.issue_description} onChange={(e) => setForm({ ...form, issue_description: e.target.value })} />
          </div>
          <div>
            <Label>Root cause</Label>
            <Textarea value={form.root_cause} onChange={(e) => setForm({ ...form, root_cause: e.target.value })} />
          </div>
          <div>
            <Label>Corrective action</Label>
            <Textarea value={form.corrective_action} onChange={(e) => setForm({ ...form, corrective_action: e.target.value })} />
          </div>
          <div>
            <Label>Preventive action</Label>
            <Textarea value={form.preventive_action} onChange={(e) => setForm({ ...form, preventive_action: e.target.value })} />
          </div>
          <div>
            <Label>Deadline</Label>
            <Input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Dialog>

      {selected && <CaDetailDialog ca={selected} onClose={() => setSelected(null)} />}
    </ProtectedShell>
  );
}

function CaDetailDialog({ ca, onClose }: { ca: CorrectiveAction; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [verificationNotes, setVerificationNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/corrective-actions/${ca.id}/verify`, { verification_notes: verificationNotes });
      await queryClient.invalidateQueries({ queryKey: ["corrective-actions"] });
      onClose();
      toast.success("Corrective action verified and closed.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  return (
    <Dialog open onClose={onClose} title={ca.title} description={formatDateTime(ca.created_at)}>
      <div className="space-y-3 text-sm">
        <div><StatusBadge status={ca.status} /></div>
        <div>
          <p className="font-medium text-ink-700">Issue</p>
          <p className="text-ink-600">{ca.issue_description}</p>
        </div>
        {ca.root_cause && <div><p className="font-medium text-ink-700">Root cause</p><p className="text-ink-600">{ca.root_cause}</p></div>}
        {ca.corrective_action && <div><p className="font-medium text-ink-700">Corrective action</p><p className="text-ink-600">{ca.corrective_action}</p></div>}
        {ca.preventive_action && <div><p className="font-medium text-ink-700">Preventive action</p><p className="text-ink-600">{ca.preventive_action}</p></div>}
        {ca.deadline && <div><p className="font-medium text-ink-700">Deadline</p><p className="text-ink-600">{formatDate(ca.deadline)}</p></div>}
        {ca.verification_notes && <div><p className="font-medium text-ink-700">Verification</p><p className="text-ink-600">{ca.verification_notes}</p></div>}
      </div>

      {ca.status !== "closed" && (
        <form onSubmit={verify} className="mt-5 space-y-3 border-t border-ink-100 pt-4">
          <Label>Verification notes</Label>
          <Textarea required value={verificationNotes} onChange={(e) => setVerificationNotes(e.target.value)} placeholder="Describe how the corrective action was verified as effective" />
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end">
            <Button type="submit">Verify &amp; Close</Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}
