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
import { api, apiErrorMessage, downloadFile } from "@/lib/api-client";
import type { Audit } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const AUDIT_TYPES = ["internal", "external", "supplier", "regulatory"];

export default function AuditsPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Audit | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", audit_type: "internal", standard: "", scope: "", scheduled_date: "" });

  const { data: audits, isLoading } = useQuery({
    queryKey: ["audits"],
    queryFn: async () => (await api.get<Audit[]>("/audits")).data,
  });

  async function createAudit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/audits", { ...form, scheduled_date: form.scheduled_date || null });
      await queryClient.invalidateQueries({ queryKey: ["audits"] });
      setCreateOpen(false);
      setForm({ title: "", audit_type: "internal", standard: "", scope: "", scheduled_date: "" });
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="Audits">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-500">Internal &amp; external audits, non-conformances, and CAPA.</p>
        <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> Schedule Audit</Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                  <th className="px-5 py-3">Title</th>
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Standard</th>
                  <th className="px-5 py-3">Scheduled</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {isLoading && <TableSkeleton columns={5} />}
                {audits?.map((a) => (
                  <tr key={a.id} className="cursor-pointer hover:bg-ink-50" onClick={() => setSelected(a)}>
                    <td className="px-5 py-3 font-medium text-ink-800">{a.title}</td>
                    <td className="px-5 py-3 capitalize text-ink-600">{a.audit_type}</td>
                    <td className="px-5 py-3 text-ink-600">{a.standard ?? "—"}</td>
                    <td className="px-5 py-3 text-ink-600">{formatDate(a.scheduled_date)}</td>
                    <td className="px-5 py-3"><StatusBadge status={a.status} /></td>
                  </tr>
                ))}
                {audits?.length === 0 && <tr><td colSpan={5} className="py-6 text-center text-ink-400">No audits scheduled yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Schedule Audit">
        <form onSubmit={createAudit} className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <Label>Type</Label>
            <Select value={form.audit_type} onChange={(e) => setForm({ ...form, audit_type: e.target.value })}>
              {AUDIT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <Label>Standard</Label>
            <Input value={form.standard} onChange={(e) => setForm({ ...form, standard: e.target.value })} placeholder="e.g. ISO 22000, BRCGS" />
          </div>
          <div>
            <Label>Scope</Label>
            <Textarea value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })} />
          </div>
          <div>
            <Label>Scheduled date</Label>
            <Input type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Schedule</Button>
          </div>
        </form>
      </Dialog>

      {selected && <AuditDetailDialog audit={selected} onClose={() => setSelected(null)} />}
    </ProtectedShell>
  );
}

function AuditDetailDialog({ audit, onClose }: { audit: Audit; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [findingOpen, setFindingOpen] = useState(false);
  const [findingForm, setFindingForm] = useState({ clause: "", severity: "minor", description: "", evidence: "" });
  const [error, setError] = useState<string | null>(null);

  async function addFinding(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/audits/${audit.id}/findings`, findingForm);
      await queryClient.invalidateQueries({ queryKey: ["audits"] });
      setFindingOpen(false);
      setFindingForm({ clause: "", severity: "minor", description: "", evidence: "" });
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  function downloadReport() {
    downloadFile(`/reports/audits/${audit.id}`, `audit-${audit.id.slice(0, 8)}.pdf`);
  }

  return (
    <Dialog open onClose={onClose} title={audit.title} description={`${audit.audit_type} · ${audit.standard ?? "No standard"}`} className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <StatusBadge status={audit.status} />
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={downloadReport}>Download PDF</Button>
          <Button size="sm" variant="outline" onClick={() => setFindingOpen(true)}><Plus className="h-3.5 w-3.5" /> Add Finding</Button>
        </div>
      </div>

      <div className="space-y-2">
        {audit.findings.length === 0 && <p className="text-sm text-ink-500">No findings recorded.</p>}
        {audit.findings.map((f) => (
          <div key={f.id} className="rounded-lg border border-ink-200 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium text-ink-800">{f.clause ?? "General"}</span>
              <StatusBadge status={f.severity} />
            </div>
            <p className="mt-1 text-ink-600">{f.description}</p>
          </div>
        ))}
      </div>

      {findingOpen && (
        <form onSubmit={addFinding} className="mt-4 space-y-3 border-t border-ink-100 pt-4">
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="Clause reference" value={findingForm.clause} onChange={(e) => setFindingForm({ ...findingForm, clause: e.target.value })} />
            <Select value={findingForm.severity} onChange={(e) => setFindingForm({ ...findingForm, severity: e.target.value })}>
              <option value="critical">Critical</option>
              <option value="major">Major</option>
              <option value="minor">Minor</option>
              <option value="observation">Observation</option>
            </Select>
          </div>
          <Textarea required placeholder="Description" value={findingForm.description} onChange={(e) => setFindingForm({ ...findingForm, description: e.target.value })} />
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setFindingOpen(false)}>Cancel</Button>
            <Button type="submit">Save Finding</Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}
