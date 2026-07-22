"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusBadge } from "@/components/ui/badge";
import { PasswordInput } from "@/components/ui/password-input";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Company, User } from "@/lib/types";
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
    </ProtectedShell>
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
