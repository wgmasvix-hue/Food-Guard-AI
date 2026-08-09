"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSearch, FileText, Plus, Search, X } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { CardGridSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { DocumentSearchResult, FGDocument } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const CATEGORIES = [
  "sop", "policy", "certificate", "specification", "supplier_document",
  "training_record", "form", "haccp_plan", "other",
];

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<FGDocument | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", category: "sop", description: "" });
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents", categoryFilter],
    queryFn: async () =>
      (
        await api.get<FGDocument[]>("/documents", {
          params: categoryFilter ? { category: categoryFilter } : undefined,
        })
      ).data,
    enabled: !searchQuery,
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ["documents-search", searchQuery],
    queryFn: async () => (await api.get<DocumentSearchResult[]>("/documents/search", { params: { q: searchQuery } })).data,
    enabled: !!searchQuery,
  });

  async function createDocument(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/documents", form);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      setCreateOpen(false);
      setForm({ title: "", category: "sop", description: "" });
      toast.success("Document created.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  return (
    <ProtectedShell title="Documents">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink-500">SOPs, policies, certificates, specifications, and training records — with version control.</p>
        <div className="flex items-center gap-2">
          <Select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="w-auto">
            <option value="">All categories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}
          </Select>
          <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New Document</Button>
        </div>
      </div>

      <form
        className="relative mb-4"
        onSubmit={(e) => {
          e.preventDefault();
          setSearchQuery(searchInput.trim());
        }}
      >
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
        <Input
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search document content — e.g. &quot;cold room cleaning&quot;"
          className="pl-9 pr-9"
        />
        {searchQuery && (
          <button
            type="button"
            onClick={() => {
              setSearchInput("");
              setSearchQuery("");
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-700"
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </form>

      {searchQuery ? (
        <div className="space-y-3">
          {searching && <p className="text-sm text-ink-400">Searching…</p>}
          {!searching && searchResults?.length === 0 && (
            <EmptyState
              icon={FileSearch}
              title={`No documents match "${searchQuery}"`}
              description="Try a different phrase, or check the spelling — search looks at each document's full content, not just its title."
            />
          )}
          {searchResults?.map((r) => (
            <Card key={r.document_id}>
              <CardContent>
                <div className="flex items-center justify-between">
                  <p className="font-medium text-ink-900">{r.title}</p>
                  <span className="text-xs capitalize text-ink-400">{r.category.replace(/_/g, " ")}</span>
                </div>
                <p className="mt-1 text-sm text-ink-600">{r.snippet}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : isLoading ? (
        <CardGridSkeleton count={6} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {documents?.length === 0 && (
            <div className="sm:col-span-2 lg:col-span-3">
              <EmptyState
                icon={FileText}
                title={categoryFilter ? `No documents in "${categoryFilter.replace(/_/g, " ")}"` : "No documents yet"}
                description={categoryFilter ? undefined : "Upload SOPs, policies, certificates, and specifications to keep them version-controlled and searchable."}
                action={categoryFilter ? undefined : { label: "New Document", onClick: () => setCreateOpen(true) }}
              />
            </div>
          )}
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
            {selected.versions.length === 0 && <EmptyState title="No versions uploaded yet" className="py-6" />}
          </div>
        </Dialog>
      )}
    </ProtectedShell>
  );
}
