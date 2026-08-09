"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Factory, Plus, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyTableRow } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/badge";
import { PasswordInput } from "@/components/ui/password-input";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/lib/toast-context";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Company, EcocashPayment, Facility, ProductionLine, Subscription, SubscriptionPlan, User } from "@/lib/types";
import { cn, roleLabel } from "@/lib/utils";

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
                {users?.length === 0 && <EmptyTableRow colSpan={4} icon={Users} title="No team members yet" />}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <BillingCard />
      <ProductionLinesCard />
    </ProtectedShell>
  );
}

function formatPrice(cents: number, currency: string) {
  if (cents === 0) return null;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() }).format(cents / 100);
}

function BillingCard() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [ecocashPlan, setEcocashPlan] = useState<SubscriptionPlan | null>(null);

  const { data: plans } = useQuery({
    queryKey: ["billing-plans"],
    queryFn: async () => (await api.get<SubscriptionPlan[]>("/billing/plans")).data,
  });
  const { data: subscription } = useQuery({
    queryKey: ["billing-subscription"],
    queryFn: async () => (await api.get<Subscription>("/billing/subscription")).data,
    retry: false,
  });
  const { data: ecocashHistory } = useQuery({
    queryKey: ["ecocash-mine"],
    queryFn: async () => (await api.get<EcocashPayment[]>("/billing/ecocash/mine")).data,
  });
  const pendingEcocash = ecocashHistory?.find((p) => p.status === "pending" || p.status === "submitted");

  function refreshEcocash() {
    queryClient.invalidateQueries({ queryKey: ["ecocash-mine"] });
    queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
  }

  async function upgrade(plan: SubscriptionPlan) {
    setLoadingPlan(plan.code);
    try {
      const { data } = await api.post("/billing/checkout", {
        plan_code: plan.code,
        success_url: window.location.href,
        cancel_url: window.location.href,
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        toast.info(data.message ?? "Checkout isn't available for this plan yet.");
      }
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setLoadingPlan(null);
    }
  }

  async function manageBilling() {
    setPortalLoading(true);
    try {
      const { data } = await api.post("/billing/portal", { return_url: window.location.href });
      if (data.portal_url) {
        window.location.href = data.portal_url;
      } else {
        toast.info(data.message ?? "Nothing to manage yet — subscribe to a paid plan first.");
      }
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setPortalLoading(false);
    }
  }

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Billing &amp; Plan</CardTitle>
        {subscription?.plan && (
          <div className="flex items-center gap-2">
            <StatusBadge status={subscription.status} />
            {subscription.plan.price_cents > 0 && (
              <Button size="sm" variant="outline" onClick={manageBilling} disabled={portalLoading}>
                {portalLoading ? "Loading…" : "Manage Billing"}
              </Button>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {subscription?.plan && (
          <p className="mb-5 text-sm text-ink-600">
            Currently on the <span className="font-semibold text-ink-900">{subscription.plan.name}</span> plan.
            {subscription.cancel_at_period_end && subscription.current_period_end && (
              <> Cancels on {new Date(subscription.current_period_end).toLocaleDateString()}.</>
            )}
            {subscription.ai_credits_remaining !== null && (
              <>
                {" "}
                <span className="font-semibold text-ink-900">{subscription.ai_credits_remaining}</span> AI credits
                left this month.
              </>
            )}
          </p>
        )}
        {pendingEcocash && (
          <p className="mb-5 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            EcoCash payment for <span className="font-semibold">{pendingEcocash.plan.name}</span> (ref{" "}
            <span className="font-mono">{pendingEcocash.reference_code}</span>) is{" "}
            {pendingEcocash.status === "pending" ? "awaiting your confirmation" : "awaiting admin review"}.
          </p>
        )}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {plans?.map((plan) => {
            const isCurrent = subscription?.plan.code === plan.code;
            const price = formatPrice(plan.price_cents, plan.currency);
            return (
              <div
                key={plan.id}
                className={cn(
                  "flex flex-col rounded-2xl border p-5 transition-shadow",
                  isCurrent ? "border-brand-500 shadow-soft" : "border-ink-200/70"
                )}
              >
                <h4 className="text-sm font-semibold text-ink-900">{plan.name}</h4>
                <p className="mt-1 text-2xl font-bold text-ink-900">
                  {price ? (
                    <>
                      {price}
                      <span className="text-sm font-normal text-ink-400">/{plan.billing_interval}</span>
                    </>
                  ) : plan.is_self_serve ? (
                    "Free"
                  ) : (
                    "Contact us"
                  )}
                </p>
                <ul className="mt-3 flex-1 space-y-1.5 text-xs text-ink-600">
                  <li className="flex items-center gap-1.5">
                    <Check className="h-3.5 w-3.5 shrink-0 text-brand-600" />
                    {plan.max_facilities ?? "Unlimited"} facilit{plan.max_facilities === 1 ? "y" : "ies"}
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="h-3.5 w-3.5 shrink-0 text-brand-600" />
                    {plan.max_employees ?? "Unlimited"} employees
                  </li>
                  {plan.ai_assistant_included && (
                    <li className="flex items-center gap-1.5">
                      <Check className="h-3.5 w-3.5 shrink-0 text-brand-600" />
                      AI Assistant —{" "}
                      {plan.ai_credits_per_month === null ? "unlimited" : `${plan.ai_credits_per_month}/mo`}
                    </li>
                  )}
                </ul>
                <Button
                  size="sm"
                  variant={isCurrent ? "outline" : "primary"}
                  className="mt-4"
                  disabled={isCurrent || loadingPlan === plan.code}
                  onClick={() => upgrade(plan)}
                >
                  {isCurrent ? "Current plan" : loadingPlan === plan.code ? "Loading…" : plan.is_self_serve ? "Upgrade" : "Contact us"}
                </Button>
                {!isCurrent && plan.is_self_serve && plan.price_cents > 0 && (
                  <Button size="sm" variant="outline" className="mt-2" onClick={() => setEcocashPlan(plan)}>
                    Pay via EcoCash
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>

      {ecocashPlan && (
        <EcocashDialog plan={ecocashPlan} onClose={() => setEcocashPlan(null)} onSubmitted={refreshEcocash} />
      )}
    </Card>
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
              {isLoading && <TableSkeleton columns={4} />}
              {lines?.map((line) => (
                <tr key={line.id}>
                  <td className="px-5 py-3 font-medium text-ink-800">{line.name}</td>
                  <td className="px-5 py-3 text-ink-600">{line.line_type ?? "—"}</td>
                  <td className="px-5 py-3 text-ink-600">{line.capacity_per_hour ?? "—"}</td>
                  <td className="px-5 py-3"><StatusBadge status={line.status} /></td>
                </tr>
              ))}
              {!isLoading && lines?.length === 0 && <EmptyTableRow colSpan={4} icon={Factory} title="No production lines yet" />}
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

function EcocashDialog({
  plan,
  onClose,
  onSubmitted,
}: {
  plan: SubscriptionPlan;
  onClose: () => void;
  onSubmitted: () => void;
}) {
  const [merchantNumber, setMerchantNumber] = useState("");
  const [payment, setPayment] = useState<EcocashPayment | null>(null);
  const [txnRef, setTxnRef] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get("/billing/ecocash/info").then(({ data }) => setMerchantNumber(data.merchant_number));
  }, []);

  async function startPayment() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<EcocashPayment>("/billing/ecocash/submit", { plan_code: plan.code });
      setPayment(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function confirmPayment(e: React.FormEvent) {
    e.preventDefault();
    if (!payment) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/billing/ecocash/${payment.id}/confirm`, {
        transaction_reference: txnRef,
        payer_phone: phone || undefined,
      });
      setDone(true);
      onSubmitted();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const price = formatPrice(plan.price_cents, plan.currency) ?? `${plan.price_cents} ${plan.currency}`;

  return (
    <Dialog
      open
      onClose={onClose}
      title={`Pay for ${plan.name} via EcoCash`}
      description="Manual mobile money payment — reviewed by an admin before your plan activates."
    >
      {done ? (
        <div className="space-y-4 text-sm text-ink-600">
          <p>Submitted for review. Your plan will update here once an admin approves it.</p>
          <Button onClick={onClose} className="w-full">Done</Button>
        </div>
      ) : !payment ? (
        <div className="space-y-4">
          <p className="text-sm text-ink-600">
            You&apos;ll send <span className="font-semibold text-ink-900">{price}</span> to EcoCash number{" "}
            <span className="font-mono font-semibold text-ink-900">{merchantNumber || "…"}</span>, then submit your
            transaction reference here for review.
          </p>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={startPayment} disabled={loading}>{loading ? "Starting…" : "Get Reference Code"}</Button>
          </div>
        </div>
      ) : (
        <form onSubmit={confirmPayment} className="space-y-4">
          <div className="rounded-lg bg-ink-50 p-3 text-sm">
            <p>
              Send <span className="font-semibold">{price}</span> to{" "}
              <span className="font-mono font-semibold">{merchantNumber}</span>
            </p>
            <p className="mt-1">
              Reference: <span className="font-mono font-semibold text-brand-700">{payment.reference_code}</span>
            </p>
          </div>
          <div>
            <Label>EcoCash transaction reference</Label>
            <Input
              required
              value={txnRef}
              onChange={(e) => setTxnRef(e.target.value)}
              placeholder="e.g. MP240101.1234.A56789"
            />
          </div>
          <div>
            <Label>Phone you paid from (optional)</Label>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="07xxxxxxxx" />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>{loading ? "Submitting…" : "Submit for Review"}</Button>
          </div>
        </form>
      )}
    </Dialog>
  );
}
