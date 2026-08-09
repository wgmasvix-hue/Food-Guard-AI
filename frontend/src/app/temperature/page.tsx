"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Thermometer } from "lucide-react";
import { useState } from "react";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/badge";
import { CardGridSkeleton, TableSkeleton } from "@/components/ui/skeleton";
import { api, apiErrorMessage } from "@/lib/api-client";
import type { TemperatureLog, TemperatureUnit } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const UNIT_TYPES = ["cold_room", "freezer", "refrigerator", "cooking", "cooling", "hot_holding"];

export default function TemperaturePage() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState<TemperatureUnit | null>(null);
  const [unitForm, setUnitForm] = useState({ name: "", unit_type: "cold_room", min_temp: "", max_temp: "", location: "" });
  const [error, setError] = useState<string | null>(null);

  const { data: units, isLoading } = useQuery({
    queryKey: ["temperature-units"],
    queryFn: async () => (await api.get<TemperatureUnit[]>("/temperature/units")).data,
  });

  async function createUnit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/temperature/units", {
        ...unitForm,
        min_temp: unitForm.min_temp ? Number(unitForm.min_temp) : null,
        max_temp: unitForm.max_temp ? Number(unitForm.max_temp) : null,
      });
      await queryClient.invalidateQueries({ queryKey: ["temperature-units"] });
      setCreateOpen(false);
      setUnitForm({ name: "", unit_type: "cold_room", min_temp: "", max_temp: "", location: "" });
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <ProtectedShell title="Temperature Monitoring">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink-500">Cold rooms, freezers, cooking, cooling, and hot holding — with automatic alerts.</p>
        <Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> New Unit</Button>
      </div>

      {isLoading ? (
        <CardGridSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {units?.length === 0 && <p className="text-sm text-ink-500">No temperature units configured yet.</p>}
          {units?.map((unit) => (
            <button key={unit.id} onClick={() => setSelectedUnit(unit)} className="text-left">
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardContent>
                  <div className="mb-2 flex items-start justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                      <Thermometer className="h-4 w-4" />
                    </span>
                    <StatusBadge status={unit.is_active ? "active" : "inactive"} />
                  </div>
                  <p className="font-medium text-ink-900">{unit.name}</p>
                  <p className="text-xs capitalize text-ink-500">{unit.unit_type.replace(/_/g, " ")} · {unit.location ?? "No location"}</p>
                  <p className="mt-2 text-sm text-ink-600">
                    Limits: {unit.min_temp ?? "—"}°C to {unit.max_temp ?? "—"}°C
                  </p>
                </CardContent>
              </Card>
            </button>
          ))}
        </div>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} title="New Temperature Unit">
        <form onSubmit={createUnit} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={unitForm.name} onChange={(e) => setUnitForm({ ...unitForm, name: e.target.value })} placeholder="e.g. Cold Room 1" />
          </div>
          <div>
            <Label>Type</Label>
            <Select value={unitForm.unit_type} onChange={(e) => setUnitForm({ ...unitForm, unit_type: e.target.value })}>
              {UNIT_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Min °C</Label>
              <Input type="number" step="any" value={unitForm.min_temp} onChange={(e) => setUnitForm({ ...unitForm, min_temp: e.target.value })} />
            </div>
            <div>
              <Label>Max °C</Label>
              <Input type="number" step="any" value={unitForm.max_temp} onChange={(e) => setUnitForm({ ...unitForm, max_temp: e.target.value })} />
            </div>
          </div>
          <div>
            <Label>Location</Label>
            <Input value={unitForm.location} onChange={(e) => setUnitForm({ ...unitForm, location: e.target.value })} />
          </div>
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Create Unit</Button>
          </div>
        </form>
      </Dialog>

      {selectedUnit && <UnitLogsDialog unit={selectedUnit} onClose={() => setSelectedUnit(null)} />}
    </ProtectedShell>
  );
}

function UnitLogsDialog({ unit, onClose }: { unit: TemperatureUnit; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [temperature, setTemperature] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: logs, isLoading } = useQuery({
    queryKey: ["temperature-logs", unit.id],
    queryFn: async () => (await api.get<TemperatureLog[]>(`/temperature/units/${unit.id}/logs`)).data,
  });

  async function submitLog(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post(`/temperature/units/${unit.id}/logs`, { temperature: Number(temperature) });
      await queryClient.invalidateQueries({ queryKey: ["temperature-logs", unit.id] });
      setTemperature("");
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <Dialog open onClose={onClose} title={unit.name} description={`Limits: ${unit.min_temp ?? "—"}°C to ${unit.max_temp ?? "—"}°C`} className="max-w-2xl">
      <form onSubmit={submitLog} className="mb-4 flex items-end gap-3">
        <div className="flex-1">
          <Label>Record temperature (°C)</Label>
          <Input type="number" step="any" required value={temperature} onChange={(e) => setTemperature(e.target.value)} />
        </div>
        <Button type="submit">Log</Button>
      </form>
      {error && <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="max-h-72 overflow-y-auto scrollbar-thin">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase text-ink-400">
              <th className="pb-2">Temp</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Recorded At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {isLoading && <TableSkeleton columns={3} />}
            {logs?.map((log) => (
              <tr key={log.id}>
                <td className="py-2 font-medium">{log.temperature}°C</td>
                <td className="py-2"><StatusBadge status={log.within_limits ? "active" : "open"} /></td>
                <td className="py-2 text-ink-500">{formatDateTime(log.recorded_at)}</td>
              </tr>
            ))}
            {logs?.length === 0 && <tr><td colSpan={3} className="py-6 text-center text-ink-400">No readings yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </Dialog>
  );
}
