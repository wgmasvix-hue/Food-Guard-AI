"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Bot, Send, Sparkles } from "lucide-react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import type { AIMessage } from "@/lib/types";

const DOCUMENT_TYPES = [
  { value: "haccp_plan", label: "HACCP Plan" },
  { value: "sop", label: "Standard Operating Procedure" },
  { value: "cleaning_procedure", label: "Cleaning Procedure" },
  { value: "policy", label: "Food Safety Policy" },
  { value: "training_material", label: "Training Material" },
  { value: "audit_report", label: "Audit Report" },
  { value: "risk_assessment", label: "Risk Assessment" },
  { value: "corrective_action", label: "Corrective Action" },
  { value: "supplier_evaluation", label: "Supplier Evaluation Form" },
];

const EXAMPLE_PROMPTS = [
  "Generate a HACCP plan for peanut butter manufacturing.",
  "Create a GMP checklist for a dairy plant.",
  "Explain ISO 22000 clause 8.5.",
];

const CHAT_EXAMPLE_PROMPTS = [
  "What are our open corrective actions right now?",
  "Any temperature excursions this week?",
  "Summarize our HACCP plans and when they're next due for review.",
  "Explain ISO 22000 clause 8.5.",
];

export default function AiAssistantPage() {
  const [mode, setMode] = useState<"generate" | "chat">("generate");

  return (
    <ProtectedShell title="AI Assistant">
      <div className="mb-4 flex gap-2">
        <Button size="sm" variant={mode === "generate" ? "primary" : "outline"} onClick={() => setMode("generate")}>
          <Sparkles className="h-4 w-4" /> Generate Document
        </Button>
        <Button size="sm" variant={mode === "chat" ? "primary" : "outline"} onClick={() => setMode("chat")}>
          <Bot className="h-4 w-4" /> Ask a Question
        </Button>
      </div>

      {mode === "generate" ? <GeneratorPanel /> : <ChatPanel />}
    </ProtectedShell>
  );
}

function GeneratorPanel() {
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0].value);
  const [prompt, setPrompt] = useState("");
  const [saveAsDocument, setSaveAsDocument] = useState(true);
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setContent(null);
    try {
      const { data } = await api.post("/ai/generate", {
        document_type: documentType,
        prompt,
        save_as_document: saveAsDocument,
      });
      setContent(data.content);
    } catch (err) {
      setError(apiErrorMessage(err, "The AI assistant is unavailable. Check that Ollama is running."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>Generate Food Safety Documentation</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={generate} className="space-y-4">
            <div>
              <Label>Document type</Label>
              <Select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                {DOCUMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </Select>
            </div>
            <div>
              <Label>Prompt</Label>
              <Textarea
                required
                rows={5}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your product, process, or requirements…"
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {EXAMPLE_PROMPTS.map((ex) => (
                  <button key={ex} type="button" onClick={() => setPrompt(ex)} className="rounded-full bg-ink-100 px-3 py-1 text-xs text-ink-600 hover:bg-ink-200">
                    {ex}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-700">
              <input type="checkbox" checked={saveAsDocument} onChange={(e) => setSaveAsDocument(e.target.checked)} />
              Save result to Documents
            </label>
            {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Generating…" : "Generate"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Result</CardTitle></CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-ink-500">Generating with AI — this can take up to a minute…</p>}
          {!loading && !content && <p className="text-sm text-ink-400">Your generated document will appear here.</p>}
          {content && (
            <div className="prose prose-sm max-w-none max-h-[60vh] overflow-y-auto scrollbar-thin">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ChatPanel() {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    const userMessage: AIMessage = { id: `local-${Date.now()}`, role: "user", content: input, created_at: new Date().toISOString() };
    setMessages((m) => [...m, userMessage]);
    setInput("");
    try {
      const { data } = await api.post("/ai/chat", { message: userMessage.content, conversation_id: conversationId });
      setConversationId(data.id);
      setMessages(data.messages);
    } catch (err) {
      setError(apiErrorMessage(err, "The AI assistant is unavailable. Check that Ollama is running."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="flex h-[70vh] flex-col">
      <CardHeader><CardTitle>Ask FoodOS</CardTitle></CardHeader>
      <CardContent className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-3 overflow-y-auto pr-1 scrollbar-thin">
          {messages.length === 0 && (
            <div className="space-y-2">
              <p className="text-sm text-ink-500">
                Ask about your company&apos;s live data (corrective actions, temperature logs, HACCP plans, GMP
                inspections, audits) or general food safety standards.
              </p>
              {CHAT_EXAMPLE_PROMPTS.map((ex) => (
                <button key={ex} onClick={() => setInput(ex)} className="block w-full rounded-lg bg-ink-50 px-3 py-2 text-left text-sm text-ink-700 hover:bg-ink-100">
                  {ex}
                </button>
              ))}
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "ml-auto bg-brand-600 text-white" : "bg-ink-100 text-ink-800"}`}>
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
          ))}
          {loading && <p className="text-sm text-ink-400">Thinking…</p>}
        </div>
        {error && <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <form onSubmit={send} className="mt-3 flex gap-2">
          <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your question…" />
          <Button type="submit" size="icon" disabled={loading}><Send className="h-4 w-4" /></Button>
        </form>
      </CardContent>
    </Card>
  );
}
