"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Sparkles } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { SignatureDialog } from "@/components/ui/signature-dialog";
import { StatusBadge } from "@/components/ui/badge";
import { TableSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage, downloadFile } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { Audit, AuditAIAnalysis, AuditTemplate } from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/utils";

const AUDIT_TYPES = ["internal", "external", "supplier", "regulatory"];

export default function AuditsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: "", audit_type: "internal", standard: "", scope: "", scheduled_date: "", template_id: "",
  });

  const { data: audits, isLoading } = useQuery({
    queryKey: ["audits"],
    queryFn: async () => (await api.get<Audit[]>("/audits")).data,
  });
  const { data: templates } = useQuery({
    queryKey: ["audit-templates"],
    queryFn: async () => (await api.get<AuditTemplate[]>("/audits/templates")).data,
  });

  async function createAudit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/audits", {
        ...form,
        scheduled_date: form.scheduled_date || null,
        template_id: form.template_id || null,
      });
      await queryClient.invalidateQueries({ queryKey: ["audits"] });
      setCreateOpen(false);
      setForm({ title: "", audit_type: "internal", standard: "", scope: "", scheduled_date: "", template_id: "" });
      toast.success("Audit scheduled.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
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
                  <tr key={a.id} className="cursor-pointer hover:bg-ink-50" onClick={() => setSelectedId(a.id)}>
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
            <Label>Template (optional)</Label>
            <Select value={form.template_id} onChange={(e) => setForm({ ...form, template_id: e.target.value })}>
              <option value="">No template — free-form audit</option>
              {templates?.map((t) => <option key={t.id} value={t.id}>{t.name} ({t.items.length} questions)</option>)}
            </Select>
            <p className="mt-1 text-xs text-ink-400">Pre-populates a structured checklist from the template&apos;s questions.</p>
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

      {selectedId && <AuditDetailDialog auditId={selectedId} onClose={() => setSelectedId(null)} />}
    </ProtectedShell>
  );
}

function AuditDetailDialog({ auditId, onClose }: { auditId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [findingOpen, setFindingOpen] = useState(false);
  const [findingForm, setFindingForm] = useState({ clause: "", severity: "minor", description: "", evidence: "" });
  const [completeSignOpen, setCompleteSignOpen] = useState(false);
  const [checklistResults, setChecklistResults] = useState<Record<string, { result: string; comment: string }>>({});
  const [error, setError] = useState<string | null>(null);
  const [signError, setSignError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const { data: audit } = useQuery({
    queryKey: ["audit", auditId],
    queryFn: async () => (await api.get<Audit>(`/audits/${auditId}`)).data,
  });
  const { data: analysis } = useQuery({
    queryKey: ["audit-ai-analysis", auditId],
    queryFn: async () => (await api.get<AuditAIAnalysis | null>(`/audits/${auditId}/ai-analysis`)).data,
  });

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["audit", auditId] });
    await queryClient.invalidateQueries({ queryKey: ["audits"] });
  }

  async function addFinding(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/audits/${auditId}/findings`, findingForm);
      await refresh();
      setFindingOpen(false);
      setFindingForm({ clause: "", severity: "minor", description: "", evidence: "" });
      toast.success("Finding added.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  function resultFor(itemId: string, fallback: string | null | undefined) {
    return checklistResults[itemId]?.result ?? fallback ?? "";
  }

  async function submitChecklist() {
    if (!audit) return;
    const items = audit.checklist_items.map((item) => ({
      id: item.id,
      result: resultFor(item.id, item.result) || "na",
      comment: checklistResults[item.id]?.comment ?? item.comment ?? undefined,
    }));
    try {
      await api.post(`/audits/${auditId}/checklist/submit`, items);
      await refresh();
      toast.success("Checklist saved.");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  }

  async function completeAudit(typedName: string) {
    setSignError(null);
    try {
      await api.post(`/audits/${auditId}/complete`, {
        entity_type: "audit", entity_id: auditId, meaning: "audit_completion", typed_name: typedName,
      });
      await refresh();
      setCompleteSignOpen(false);
      toast.success("Audit completed and signed.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setSignError(message);
      toast.error(message);
    }
  }

  async function runAnalysis() {
    setAnalyzing(true);
    try {
      await api.post(`/audits/${auditId}/ai-analysis`);
      await queryClient.invalidateQueries({ queryKey: ["audit-ai-analysis", auditId] });
      toast.success("AI analysis generated.");
    } catch (err) {
      toast.error(apiErrorMessage(err, "AI assistant unavailable — check that Ollama is running."));
    } finally {
      setAnalyzing(false);
    }
  }

  function downloadReport() {
    downloadFile(`/reports/audits/${auditId}`, `audit-${auditId.slice(0, 8)}.pdf`);
  }

  if (!audit) return null;

  return (
    <Dialog open onClose={onClose} title={audit.title} description={`${audit.audit_type} · ${audit.standard ?? "No standard"}`} className="max-w-2xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <StatusBadge status={audit.status} />
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={downloadReport}>Download PDF</Button>
          <Button size="sm" variant="outline" onClick={() => setFindingOpen(true)}><Plus className="h-3.5 w-3.5" /> Add Finding</Button>
          {audit.status !== "completed" && (
            <Button size="sm" onClick={() => setCompleteSignOpen(true)}>Complete &amp; Sign</Button>
          )}
        </div>
      </div>

      {audit.checklist_items.length > 0 && (
        <div className="mb-5 space-y-2 border-b border-ink-100 pb-4">
          <p className="text-sm font-medium text-ink-700">Checklist</p>
          {audit.checklist_items.map((item) => (
            <div key={item.id} className="rounded-lg border border-ink-200 p-3">
              <p className="text-sm font-medium text-ink-800">
                {item.clause && <span className="text-ink-400">{item.clause} · </span>}
                {item.question}
                {item.is_critical && <span className="ml-1 text-xs font-semibold text-red-600">(critical)</span>}
              </p>
              <div className="mt-2 flex gap-2">
                {["pass", "fail", "na"].map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setChecklistResults({ ...checklistResults, [item.id]: { comment: checklistResults[item.id]?.comment ?? item.comment ?? "", result: opt } })}
                    className={`rounded-md px-3 py-1 text-xs font-medium capitalize ${
                      resultFor(item.id, item.result) === opt
                        ? opt === "pass" ? "bg-brand-600 text-white" : opt === "fail" ? "bg-red-600 text-white" : "bg-ink-600 text-white"
                        : "bg-ink-100 text-ink-600 hover:bg-ink-200"
                    }`}
                  >
                    {opt === "na" ? "N/A" : opt}
                  </button>
                ))}
              </div>
              {item.corrective_action_id && (
                <p className="mt-2 text-xs text-amber-700">Corrective action auto-created from this failure.</p>
              )}
            </div>
          ))}
          <div className="flex justify-end">
            <Button size="sm" variant="outline" onClick={submitChecklist}>Save Checklist</Button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <p className="text-sm font-medium text-ink-700">Findings</p>
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

      <div className="mt-5 border-t border-ink-100 pt-4">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-sm font-medium text-ink-700">AI Analysis</p>
          <Button size="sm" variant="outline" onClick={runAnalysis} disabled={analyzing}>
            <Sparkles className="h-3.5 w-3.5" /> {analyzing ? "Analyzing…" : analysis ? "Re-analyze" : "Analyze with AI"}
          </Button>
        </div>
        {analysis ? (
          <div className="space-y-3 rounded-lg bg-ink-50 p-3 text-sm">
            <div className="flex items-center gap-2">
              <StatusBadge status={analysis.risk_level === "low" ? "active" : analysis.risk_level === "critical" || analysis.risk_level === "high" ? "open" : "in_progress"} />
              <span className="text-xs text-ink-400">Generated {formatDateTime(analysis.generated_at)}</span>
            </div>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{analysis.summary}</ReactMarkdown>
            </div>
            {analysis.root_cause_analysis && (
              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-ink-700">Root Cause Analysis</summary>
                <div className="prose prose-sm mt-2 max-w-none"><ReactMarkdown>{analysis.root_cause_analysis}</ReactMarkdown></div>
              </details>
            )}
            {analysis.recommended_corrective_actions && (
              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-ink-700">Recommended Corrective Actions</summary>
                <div className="prose prose-sm mt-2 max-w-none"><ReactMarkdown>{analysis.recommended_corrective_actions}</ReactMarkdown></div>
              </details>
            )}
            {analysis.improvement_plan && (
              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-ink-700">Improvement Plan</summary>
                <div className="prose prose-sm mt-2 max-w-none"><ReactMarkdown>{analysis.improvement_plan}</ReactMarkdown></div>
              </details>
            )}
          </div>
        ) : (
          <p className="text-sm text-ink-500">No AI analysis yet — generate one to get a summary, risk level, root cause, and improvement plan.</p>
        )}
      </div>

      <SignatureDialog
        open={completeSignOpen}
        onClose={() => setCompleteSignOpen(false)}
        onSign={completeAudit}
        meaning="audit_completion"
        title="Complete Audit"
        error={signError}
      />
    </Dialog>
  );
}
