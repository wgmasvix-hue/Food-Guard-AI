"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { SignatureDialog } from "@/components/ui/signature-dialog";
import { StatusBadge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { api, apiErrorMessage } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type { CCP, HaccpPlan, Hazard, MonitoringRecord } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const HAZARD_TYPES = ["biological", "chemical", "physical", "allergen", "radiological"];

export default function HaccpPlanDetailPage() {
  const params = useParams<{ planId: string }>();
  const planId = params.planId;
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: plan } = useQuery({
    queryKey: ["haccp-plan", planId],
    queryFn: async () => (await api.get<HaccpPlan>(`/haccp/plans/${planId}`)).data,
  });
  const { data: hazards } = useQuery({
    queryKey: ["haccp-hazards", planId],
    queryFn: async () => (await api.get<Hazard[]>(`/haccp/plans/${planId}/hazards`)).data,
  });
  const { data: ccps } = useQuery({
    queryKey: ["haccp-ccps", planId],
    queryFn: async () => (await api.get<CCP[]>(`/haccp/plans/${planId}/ccps`)).data,
  });

  const [hazardOpen, setHazardOpen] = useState(false);
  const [ccpOpen, setCcpOpen] = useState(false);
  const [selectedCcp, setSelectedCcp] = useState<CCP | null>(null);
  const [approveSignOpen, setApproveSignOpen] = useState(false);
  const [approveError, setApproveError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [hazardForm, setHazardForm] = useState({
    process_step: "", hazard_type: "biological", description: "", likelihood: 1, severity: 1,
    control_measures: "", is_ccp: false,
  });
  const [ccpForm, setCcpForm] = useState({
    number: "", name: "", critical_limit_min: "", critical_limit_max: "", critical_limit_unit: "",
    monitoring_procedure: "", monitoring_frequency: "", corrective_action_procedure: "",
  });

  async function approvePlan(typedName: string) {
    setApproveError(null);
    try {
      await api.post(`/haccp/plans/${planId}/approve`, {
        entity_type: "haccp_plan",
        entity_id: planId,
        meaning: "haccp_plan_approval",
        typed_name: typedName,
      });
      await queryClient.invalidateQueries({ queryKey: ["haccp-plan", planId] });
      setApproveSignOpen(false);
      toast.success("HACCP plan approved and signed.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setApproveError(message);
      toast.error(message);
    }
  }

  async function createHazard(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/haccp/plans/${planId}/hazards`, hazardForm);
      await queryClient.invalidateQueries({ queryKey: ["haccp-hazards", planId] });
      setHazardOpen(false);
      setHazardForm({ process_step: "", hazard_type: "biological", description: "", likelihood: 1, severity: 1, control_measures: "", is_ccp: false });
      toast.success("Hazard added.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  async function createCcp(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/haccp/plans/${planId}/ccps`, {
        ...ccpForm,
        critical_limit_min: ccpForm.critical_limit_min ? Number(ccpForm.critical_limit_min) : null,
        critical_limit_max: ccpForm.critical_limit_max ? Number(ccpForm.critical_limit_max) : null,
      });
      await queryClient.invalidateQueries({ queryKey: ["haccp-ccps", planId] });
      setCcpOpen(false);
      setCcpForm({ number: "", name: "", critical_limit_min: "", critical_limit_max: "", critical_limit_unit: "", monitoring_procedure: "", monitoring_frequency: "", corrective_action_procedure: "" });
      toast.success("Critical Control Point added.");
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  return (
    <ProtectedShell title={plan?.name ?? "HACCP Plan"}>
      {plan && (
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusBadge status={plan.status} />
            <span className="text-sm text-ink-500">Version {plan.version}</span>
          </div>
          {plan.status !== "approved" && (
            <Button size="sm" variant="secondary" onClick={() => setApproveSignOpen(true)}>Approve Plan</Button>
          )}
        </div>
      )}

      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Hazard Analysis</CardTitle>
          <Button size="sm" variant="outline" onClick={() => setHazardOpen(true)}><Plus className="h-4 w-4" /> Add Hazard</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase text-ink-400">
                  <th className="pb-2">Process Step</th>
                  <th className="pb-2">Type</th>
                  <th className="pb-2">Description</th>
                  <th className="pb-2">Risk Score</th>
                  <th className="pb-2">CCP?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-100">
                {hazards?.map((h) => (
                  <tr key={h.id}>
                    <td className="py-2 font-medium text-ink-800">{h.process_step}</td>
                    <td className="py-2 capitalize text-ink-600">{h.hazard_type}</td>
                    <td className="py-2 text-ink-600">{h.description}</td>
                    <td className="py-2 text-ink-600">{h.risk_score}</td>
                    <td className="py-2">{h.is_ccp ? <StatusBadge status="active" /> : <span className="text-ink-400">No</span>}</td>
                  </tr>
                ))}
                {hazards?.length === 0 && (
                  <tr><td colSpan={5} className="py-6 text-center text-ink-400">No hazards recorded yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Critical Control Points</CardTitle>
          <Button size="sm" variant="outline" onClick={() => setCcpOpen(true)}><Plus className="h-4 w-4" /> Add CCP</Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {ccps?.length === 0 && <p className="text-sm text-ink-500">No CCPs defined yet.</p>}
          {ccps?.map((ccp) => (
            <button
              key={ccp.id}
              onClick={() => setSelectedCcp(ccp)}
              className="flex w-full items-center justify-between rounded-lg border border-ink-200 px-4 py-3 text-left hover:bg-ink-50"
            >
              <div>
                <p className="font-medium text-ink-900">{ccp.number} — {ccp.name}</p>
                <p className="text-xs text-ink-500">
                  Limit: {ccp.critical_limit_min ?? "—"} to {ccp.critical_limit_max ?? "—"} {ccp.critical_limit_unit ?? ""}
                </p>
              </div>
              <StatusBadge status={ccp.status} />
            </button>
          ))}
        </CardContent>
      </Card>

      <Dialog open={hazardOpen} onClose={() => setHazardOpen(false)} title="Add Hazard">
        <form onSubmit={createHazard} className="space-y-4">
          <div>
            <Label>Process step</Label>
            <Input required value={hazardForm.process_step} onChange={(e) => setHazardForm({ ...hazardForm, process_step: e.target.value })} />
          </div>
          <div>
            <Label>Hazard type</Label>
            <Select value={hazardForm.hazard_type} onChange={(e) => setHazardForm({ ...hazardForm, hazard_type: e.target.value })}>
              {HAZARD_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </Select>
          </div>
          <div>
            <Label>Description</Label>
            <Textarea required value={hazardForm.description} onChange={(e) => setHazardForm({ ...hazardForm, description: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Likelihood (1-5)</Label>
              <Input type="number" min={1} max={5} value={hazardForm.likelihood} onChange={(e) => setHazardForm({ ...hazardForm, likelihood: Number(e.target.value) })} />
            </div>
            <div>
              <Label>Severity (1-5)</Label>
              <Input type="number" min={1} max={5} value={hazardForm.severity} onChange={(e) => setHazardForm({ ...hazardForm, severity: Number(e.target.value) })} />
            </div>
          </div>
          <div>
            <Label>Control measures</Label>
            <Textarea value={hazardForm.control_measures} onChange={(e) => setHazardForm({ ...hazardForm, control_measures: e.target.value })} />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink-700">
            <input type="checkbox" checked={hazardForm.is_ccp} onChange={(e) => setHazardForm({ ...hazardForm, is_ccp: e.target.checked })} />
            This hazard requires a Critical Control Point
          </label>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setHazardOpen(false)}>Cancel</Button>
            <Button type="submit">Save Hazard</Button>
          </div>
        </form>
      </Dialog>

      <Dialog open={ccpOpen} onClose={() => setCcpOpen(false)} title="Add Critical Control Point">
        <form onSubmit={createCcp} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Number</Label>
              <Input required placeholder="CCP-1" value={ccpForm.number} onChange={(e) => setCcpForm({ ...ccpForm, number: e.target.value })} />
            </div>
            <div>
              <Label>Name</Label>
              <Input required value={ccpForm.name} onChange={(e) => setCcpForm({ ...ccpForm, name: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>Min limit</Label>
              <Input type="number" step="any" value={ccpForm.critical_limit_min} onChange={(e) => setCcpForm({ ...ccpForm, critical_limit_min: e.target.value })} />
            </div>
            <div>
              <Label>Max limit</Label>
              <Input type="number" step="any" value={ccpForm.critical_limit_max} onChange={(e) => setCcpForm({ ...ccpForm, critical_limit_max: e.target.value })} />
            </div>
            <div>
              <Label>Unit</Label>
              <Input placeholder="°C" value={ccpForm.critical_limit_unit} onChange={(e) => setCcpForm({ ...ccpForm, critical_limit_unit: e.target.value })} />
            </div>
          </div>
          <div>
            <Label>Monitoring procedure</Label>
            <Textarea value={ccpForm.monitoring_procedure} onChange={(e) => setCcpForm({ ...ccpForm, monitoring_procedure: e.target.value })} />
          </div>
          <div>
            <Label>Monitoring frequency</Label>
            <Input value={ccpForm.monitoring_frequency} onChange={(e) => setCcpForm({ ...ccpForm, monitoring_frequency: e.target.value })} placeholder="e.g. every 2 hours" />
          </div>
          <div>
            <Label>Corrective action procedure</Label>
            <Textarea value={ccpForm.corrective_action_procedure} onChange={(e) => setCcpForm({ ...ccpForm, corrective_action_procedure: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCcpOpen(false)}>Cancel</Button>
            <Button type="submit">Save CCP</Button>
          </div>
        </form>
      </Dialog>

      {selectedCcp && (
        <CcpMonitoringDialog ccp={selectedCcp} onClose={() => setSelectedCcp(null)} />
      )}

      <SignatureDialog
        open={approveSignOpen}
        onClose={() => setApproveSignOpen(false)}
        onSign={approvePlan}
        meaning="haccp_plan_approval"
        title="Approve HACCP Plan"
        error={approveError}
      />
    </ProtectedShell>
  );
}

function CcpMonitoringDialog({ ccp, onClose }: { ccp: CCP; onClose: () => void }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: records, isLoading } = useQuery({
    queryKey: ["ccp-monitoring", ccp.id],
    queryFn: async () => (await api.get<MonitoringRecord[]>(`/haccp/ccps/${ccp.id}/monitoring`)).data,
  });

  async function submitReading(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const { data } = await api.post(`/haccp/ccps/${ccp.id}/monitoring`, { measured_value: Number(value) });
      await queryClient.invalidateQueries({ queryKey: ["ccp-monitoring", ccp.id] });
      setValue("");
      if (data.within_limits) {
        toast.success("Reading logged — within limits.");
      } else {
        toast.error("Reading is outside critical limits — a corrective action was created.");
      }
    } catch (err) {
      const message = apiErrorMessage(err);
      setError(message);
      toast.error(message);
    }
  }

  return (
    <Dialog open onClose={onClose} title={`${ccp.number} — ${ccp.name}`} description={ccp.critical_limit_description ?? undefined} className="max-w-2xl">
      <form onSubmit={submitReading} className="mb-4 flex items-end gap-3">
        <div className="flex-1">
          <Label>Record a reading {ccp.critical_limit_unit ? `(${ccp.critical_limit_unit})` : ""}</Label>
          <Input type="number" step="any" required value={value} onChange={(e) => setValue(e.target.value)} />
        </div>
        <Button type="submit">Log Reading</Button>
      </form>
      {error && <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="max-h-72 overflow-y-auto scrollbar-thin">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-ink-400">
              <th className="pb-2">Value</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Recorded At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {isLoading && <tr><td colSpan={3} className="py-4 text-center text-ink-400">Loading…</td></tr>}
            {records?.map((r) => (
              <tr key={r.id}>
                <td className="py-2">{r.measured_value} {r.unit}</td>
                <td className="py-2">
                  <StatusBadge status={r.within_limits ? "active" : "open"} />
                </td>
                <td className="py-2 text-ink-500">{formatDateTime(r.recorded_at)}</td>
              </tr>
            ))}
            {records?.length === 0 && <tr><td colSpan={3} className="py-6 text-center text-ink-400">No readings yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </Dialog>
  );
}
