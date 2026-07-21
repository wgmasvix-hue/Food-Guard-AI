"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import type { FGDocument } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const CATEGORIES = [
  "sop", "policy", "certificate", "specification", "supplier_document",
  "training_record", "form", "haccp_plan", "other",
];

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<FGDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", category: "sop", description: "" });

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: async () => (await api.get<FGDocument[]>("/documents")).data,
  });

  async function createDocument(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/documents", form);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      setCreateOpen(false);
      setForm({ title: "", category: "sop", description: "" });
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="Documents">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-ink-500">SOPs, policies, certificates, specifications, and training records — with version control.</p>
        <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New Document</Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-ink-500">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {documents?.length === 0 && <p className="text-sm text-ink-500">No documents yet.</p>}
          {documents?.map((doc) => (
            <button key={doc.id} onClick={() => setSelected(doc)} className="text-left">
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardContent>
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-ink-100 text-ink-700">
                    <FileText className="h-4 w-4" />
                  </span>
                  <p className="mt-2 font-medium text-ink-900">{doc.title}</p>
                  <p className="text-xs capitalize text-ink-500">{doc.category.replace(/_/g, " ")}</p>
                  <p className="mt-2 text-xs text-ink-400">
                    {doc.versions.length} version{doc.versions.length === 1 ? "" : "s"}
                    {doc.expires_on ? ` · Expires ${formatDate(doc.expires_on)}` : ""}
                  </p>
                </CardContent>
              </Card>
            </button>
          ))}
        </div>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="New Document">
        <form onSubmit={createDocument} className="space-y-4">
          <div>
            <Label>Title</Label>
            <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <Label>Category</Label>
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
            </Select>
          </div>
          <div>
            <Label>Description</Label>
            <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Dialog>

      {selected && (
        <Dialog open onClose={() => setSelected(null)} title={selected.title} description={selected.category.replace(/_/g, " ")} className="max-w-2xl">
          <p className="mb-4 text-sm text-ink-600">{selected.description || "No description."}</p>
          <div className="space-y-2">
            {selected.versions.map((v) => (
              <div key={v.id} className="rounded-lg border border-ink-200 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-ink-800">Version {v.version}</span>
                  <span className="text-xs text-ink-400">{formatDate(v.created_at)}</span>
                </div>
                {v.content_text ? (
                  <pre className="mt-2 max-h-64 overflow-y-auto whitespace-pre-wrap text-xs text-ink-600 scrollbar-thin">{v.content_text}</pre>
                ) : (
                  <p className="mt-1 text-xs text-ink-500">{v.file_name ?? "No file attached"}</p>
                )}
              </div>
            ))}
            {selected.versions.length === 0 && <p className="text-sm text-ink-500">No versions uploaded yet.</p>}
          </div>
        </Dialog>
      )}
    </ProtectedShell>
  );
}
