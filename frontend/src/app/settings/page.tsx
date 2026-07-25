"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/badge";
import { PasswordInput } from "@/components/ui/password-input";
import { useToast } from "@/lib/toast-context";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Company, Facility, ProductionLine, User } from "@/lib/types";
import { roleLabel } from "@/lib/utils";

export default function SettingsPage() {
  const { user } = useAuth();

  const { data: company } = useQuery({
    queryKey: ["company-me"],
    queryFn: async () => (await api.get<Company>("/companies/me")).data,
    enabled: !!user?.company_id,
  });
  const { data: users } = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<User[]>("/users")).data,
  });

  return (
    <ProtectedShell title="Settings">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Company</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><span className="font-medium text-ink-700">Name:</span> {company?.name ?? "—"}</p>
            <p><span className="font-medium text-ink-700">Industry:</span> {company?.industry ?? "—"}</p>
            <p><span className="font-medium text-ink-700">Country:</span> {company?.country ?? "—"}</p>
          </CardContent>
        </Card>

        <ChangePasswordCard />
      </div>

      <Card className="mt-6">
        <CardHeader><CardTitle>Team Members</CardTitle></CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Email</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {users?.map((u) => (
                  <tr key={u.id}>
                    <td className="px-5 py-3 font-medium text-ink-800">{u.full_name}</td>
                    <td className="px-5 py-3 text-ink-600">{u.email}</td>
                    <td className="px-5 py-3 text-ink-600">{roleLabel(u.role)}</td>
                    <td className="px-5 py-3"><StatusBadge status={u.is_active ? "active" : "inactive"} /></td>
                  </tr>
                ))}
                {users?.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-ink-400">No team members yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <ProductionLinesCard />
    </ProtectedShell>
  );
}

function ProductionLinesCard() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [facilityId, setFacilityId] = useState<string>("");
  const [createOpen, setCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", line_type: "", capacity_per_hour: "" });

  const { data: facilities } = useQuery({
    queryKey: ["facilities"],
    queryFn: async () => (await api.get<Facility[]>("/companies/facilities")).data,
  });
  const activeFacilityId = facilityId || facilities?.[0]?.id || "";

  const { data: lines, isLoading } = useQuery({
    queryKey: ["production-lines", activeFacilityId],
    queryFn: async () =>
      (await api.get<ProductionLine[]>(`/companies/facilities/${activeFacilityId}/production-lines`)).data,
    enabled: !!activeFacilityId,
  });

  async function createLine(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/companies/facilities/${activeFacilityId}/production-lines`, {
        ...form,
        capacity_per_hour: form.capacity_per_hour ? Number(form.capacity_per_hour) : null,
      });
      await queryClient.invalidateQueries({ queryKey: ["production-lines", activeFacilityId] });
      setCreateOpen(false);
      setForm({ name: "", line_type: "", capacity_per_hour: "" });
      toast.success("Production line added.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  if (!facilities || facilities.length === 0) return null;

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Production Lines</CardTitle>
        <div className="flex items-center gap-2">
          <Select value={activeFacilityId} onChange={(e) => setFacilityId(e.target.value)} className="w-auto">
            {facilities.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </Select>
          <Button size="sm" onClick={() => setCreateOpen(true)}><Plus className="h-3.5 w-3.5" /> Add Line</Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink-100 text-xs uppercase text-ink-400">
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Capacity/hr</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {isLoading && <tr><td colSpan={4} className="py-6 text-center text-ink-400">Loading…</td></tr>}
              {lines?.map((line) => (
                <tr key={line.id}>
                  <td className="px-5 py-3 font-medium text-ink-800">{line.name}</td>
                  <td className="px-5 py-3 text-ink-600">{line.line_type ?? "—"}</td>
                  <td className="px-5 py-3 text-ink-600">{line.capacity_per_hour ?? "—"}</td>
                  <td className="px-5 py-3"><StatusBadge status={line.status} /></td>
                </tr>
              ))}
              {lines?.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-ink-400">No production lines yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </CardContent>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="Add Production Line">
        <form onSubmit={createLine} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Packaging Line 1" />
          </div>
          <div>
            <Label>Line type</Label>
            <Input value={form.line_type} onChange={(e) => setForm({ ...form, line_type: e.target.value })} placeholder="e.g. packaging, mixing, filling" />
          </div>
          <div>
            <Label>Capacity per hour</Label>
            <Input type="number" step="any" value={form.capacity_per_hour} onChange={(e) => setForm({ ...form, capacity_per_hour: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Add Line</Button>
          </div>
        </form>
      </Dialog>
    </Card>
  );
}

function ChangePasswordCard() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await api.post("/auth/password-change", { current_password: currentPassword, new_password: newPassword });
      setMessage({ type: "success", text: "Password updated." });
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setMessage({ type: "error", text: apiErrorMessage(err) });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <Label>Current password</Label>
            <PasswordInput required value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div>
            <Label>New password</Label>
            <PasswordInput required minLength={8} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          {message && (
            <p className={`rounded-md px-3 py-2 text-sm ${message.type === "success" ? "bg-brand-50 text-brand-800" : "bg-red-50 text-red-700"}`}>
              {message.text}
            </p>
          )}
          <Button type="submit" disabled={saving}>{saving ? "Updating…" : "Update Password"}</Button>
        </form>
      </CardContent>
    </Card>
  );
}
