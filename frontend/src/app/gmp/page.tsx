"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ListChecks, Play } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { StatusBadge } from "@/components/ui/badge";
import { Skeleton, TableSkeleton } from "@/components/ui/skeleton";
import { api, apiErrorMessage } from "@/lib/api-client";
import type { Checklist, ChecklistTemplate } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function GmpPage() {
  const queryClient = useQueryClient();
  const [activeChecklist, setActiveChecklist] = useState<Checklist | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: templates, isLoading: loadingTemplates } = useQuery({
    queryKey: ["gmp-templates"],
    queryFn: async () => (await api.get<ChecklistTemplate[]>("/gmp/templates")).data,
  });
  const { data: checklists, isLoading: loadingChecklists } = useQuery({
    queryKey: ["gmp-checklists"],
    queryFn: async () => (await api.get<Checklist[]>("/gmp/checklists")).data,
  });

  async function startChecklist(templateId: string) {
    setError(null);
    try {
      const { data } = await api.post<Checklist>("/gmp/checklists", { template_id: templateId });
      setActiveChecklist(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="GMP Inspections">
      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><ListChecks className="h-4 w-4" /> Checklist Templates</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingTemplates ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {templates?.map((t) => (
                <div key={t.id} className="flex items-center justify-between rounded-lg border border-ink-200 px-4 py-3">
                  <div>
                    <p className="font-medium text-ink-900">{t.name}</p>
                    <p className="text-xs capitalize text-ink-500">{t.category.replace(/_/g, " ")} · {t.frequency ?? "ad hoc"}</p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => startChecklist(t.id)}>
                    <Play className="h-3.5 w-3.5" /> Start
                  </Button>
                </div>
              ))}
              {templates?.length === 0 && <p className="text-sm text-ink-500">No templates yet.</p>}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Inspection History</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Mobile card list */}
          <div className="divide-y divide-ink-100 sm:hidden">
            {loadingChecklists && <div className="py-6 text-center text-sm text-ink-400">Loading…</div>}
            {checklists?.map((c) => (
              <div key={c.id} className="flex items-start justify-between py-3">
                <div>
                  <StatusBadge status={c.status} />
                  <p className="mt-1 text-xs text-ink-500">{formatDateTime(c.started_at)}</p>
                  {c.score != null && <p className="text-xs text-ink-700">Score: {c.score}%</p>}
                </div>
                {c.status === "in_progress" && (
                  <Button size="sm" variant="ghost" onClick={() => setActiveChecklist(c)}>Continue</Button>
                )}
              </div>
            ))}
            {checklists?.length === 0 && (
              <p className="py-6 text-center text-sm text-ink-400">No inspections yet.</p>
            )}
          </div>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase text-ink-400">
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Started</th>
                  <th className="pb-2">Completed</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {loadingChecklists && <TableSkeleton columns={5} />}
                {checklists?.map((c) => (
                  <tr key={c.id}>
                    <td className="py-2"><StatusBadge status={c.status} /></td>
                    <td className="py-2 text-ink-700">{c.score != null ? `${c.score}%` : "—"}</td>
                    <td className="py-2 text-ink-500">{formatDateTime(c.started_at)}</td>
                    <td className="py-2 text-ink-500">{formatDateTime(c.completed_at)}</td>
                    <td className="py-2 text-right">
                      {c.status === "in_progress" && (
                        <Button size="sm" variant="ghost" onClick={() => setActiveChecklist(c)}>Continue</Button>
                      )}
                    </td>
                  </tr>
                ))}
                {checklists?.length === 0 && <tr><td colSpan={5} className="py-6 text-center text-ink-400">No inspections yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {activeChecklist && (
        <ChecklistDialog
          checklist={activeChecklist}
          onClose={() => setActiveChecklist(null)}
          onSubmitted={() => {
            setActiveChecklist(null);
            queryClient.invalidateQueries({ queryKey: ["gmp-checklists"] });
          }}
        />
      )}
    </ProtectedShell>
  );
}

function ChecklistDialog({
  checklist,
  onClose,
  onSubmitted,
}: {
  checklist: Checklist;
  onClose: () => void;
  onSubmitted: () => void;
}) {
  const [results, setResults] = useState<Record<string, { result: string; comment: string }>>(
    Object.fromEntries(checklist.items.map((i) => [i.id, { result: i.result ?? "", comment: i.comment ?? "" }]))
  );
  const [notes, setNotes] = useState(checklist.notes ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post(`/gmp/checklists/${checklist.id}/submit`, {
        notes,
        items: Object.entries(results).map(([id, r]) => ({ id, result: r.result || "na", comment: r.comment })),
      });
      onSubmitted();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open onClose={onClose} title="Complete Inspection" className="max-w-2xl">
      <form onSubmit={submit} className="space-y-4">
        {checklist.items.map((item) => (
          <div key={item.id} className="rounded-lg border border-ink-200 p-3">
            <p className="text-sm font-medium text-ink-800">
              {item.question} {item.is_critical && <span className="ml-1 text-xs font-semibold text-red-600">(critical)</span>}
            </p>
            <div className="mt-2 flex gap-2">
              {["pass", "fail", "na"].map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setResults({ ...results, [item.id]: { ...results[item.id], result: opt } })}
                  className={`rounded-md px-3 py-1 text-xs font-medium capitalize ${
                    results[item.id]?.result === opt
                      ? opt === "pass" ? "bg-brand-600 text-white" : opt === "fail" ? "bg-red-600 text-white" : "bg-ink-600 text-white"
                      : "bg-ink-100 text-ink-600 hover:bg-ink-200"
                  }`}
                >
                  {opt === "na" ? "N/A" : opt}
                </button>
              ))}
            </div>
            {results[item.id]?.result === "fail" && (
              <Textarea
                className="mt-2"
                placeholder="Comment (required for failures — creates a corrective action)"
                value={results[item.id]?.comment ?? ""}
                onChange={(e) => setResults({ ...results, [item.id]: { ...results[item.id], comment: e.target.value } })}
              />
            )}
          </div>
        ))}
        <div>
          <Textarea placeholder="Overall notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={saving}>{saving ? "Submitting…" : "Submit Inspection"}</Button>
        </div>
      </form>
    </Dialog>
  );
}
