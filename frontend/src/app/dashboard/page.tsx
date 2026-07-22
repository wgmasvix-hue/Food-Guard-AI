"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Gauge,
  ListChecks,
  Thermometer,
} from "lucide-react";
import Link from "next/link";

import { ProtectedShell } from "@/components/layout/protected-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import type { DashboardSummary } from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/utils";

function ScoreRing({ score }: { score: number }) {
  const color = score >= 90 ? "text-brand-600" : score >= 75 ? "text-amber-500" : "text-red-500";
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <svg className="h-32 w-32 -rotate-90">
        <circle cx="64" cy="64" r="42" strokeWidth="10" className="stroke-ink-100" fill="none" />
        <circle
          cx="64"
          cy="64"
          r="42"
          strokeWidth="10"
          strokeLinecap="round"
          className={color}
          stroke="currentColor"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="absolute text-2xl font-bold text-ink-900">{score}%</span>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  tone = "default",
}: {
  icon: typeof Gauge;
  label: string;
  value: number | string;
  tone?: "default" | "warning" | "danger";
}) {
  const toneClasses =
    tone === "danger" ? "text-red-600 bg-red-50" : tone === "warning" ? "text-amber-600 bg-amber-50" : "text-brand-700 bg-brand-50";
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <span className={`flex h-11 w-11 items-center justify-center rounded-lg ${toneClasses}`}>
          <Icon className="h-5 w-5" />
        </span>
        <div>
          <p className="text-2xl font-semibold text-ink-900">{value}</p>
          <p className="text-sm text-ink-500">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
  });

  return (
    <ProtectedShell title="Dashboard">
      {isLoading || !data ? (
        <DashboardSkeleton />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card className="md:col-span-1">
              <CardContent className="flex flex-col items-center justify-center gap-2 py-6">
                <ScoreRing score={data.compliance_score} />
                <p className="text-sm font-medium text-ink-600">Compliance Score</p>
              </CardContent>
            </Card>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 md:col-span-3">
              <StatTile icon={ClipboardList} label="Open Corrective Actions" value={data.open_corrective_actions} tone={data.open_corrective_actions > 0 ? "warning" : "default"} />
              <StatTile icon={AlertTriangle} label="Overdue Corrective Actions" value={data.overdue_corrective_actions} tone={data.overdue_corrective_actions > 0 ? "danger" : "default"} />
              <StatTile icon={Thermometer} label="Temperature Alerts Today" value={data.temperature_alerts_today} tone={data.temperature_alerts_today > 0 ? "danger" : "default"} />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><ListChecks className="h-4 w-4" /> Today&apos;s Tasks</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.today_tasks.map((task, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-ink-700">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />
                    {task}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Bot className="h-4 w-4" /> AI Recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.ai_recommendations.map((rec, i) => (
                  <div key={i} className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-800">
                    {rec}
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><CalendarClock className="h-4 w-4" /> Upcoming Audits</CardTitle>
                <Link href="/audits" className="text-xs font-medium text-brand-700 hover:underline">View all</Link>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.upcoming_audits.length === 0 && <p className="text-sm text-ink-500">No audits scheduled.</p>}
                {data.upcoming_audits.map((audit) => (
                  <div key={audit.id} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium text-ink-800">{audit.title}</p>
                      <p className="text-xs text-ink-500">{formatDate(audit.scheduled_date)}</p>
                    </div>
                    <StatusBadge status={audit.status} />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Inspections</CardTitle>
                <Link href="/gmp" className="text-xs font-medium text-brand-700 hover:underline">View all</Link>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.recent_inspections.length === 0 && <p className="text-sm text-ink-500">No inspections yet.</p>}
                {data.recent_inspections.map((c) => (
                  <div key={c.id} className="flex items-center justify-between text-sm">
                    <div>
                      <p className="font-medium text-ink-800">Checklist #{c.id.slice(0, 8)}</p>
                      <p className="text-xs text-ink-500">{formatDateTime(c.completed_at)} · Score {c.score ?? "—"}%</p>
                    </div>
                    <StatusBadge status={c.status} />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Temperature Alerts</CardTitle>
                <Link href="/temperature" className="text-xs font-medium text-brand-700 hover:underline">View all</Link>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.recent_temperature_alerts.length === 0 && <p className="text-sm text-ink-500">No recent alerts.</p>}
                {data.recent_temperature_alerts.map((log) => (
                  <div key={log.id} className="flex items-center justify-between text-sm">
                    <p className="text-ink-700">{formatDateTime(log.recorded_at)}</p>
                    <span className="font-semibold text-red-600">{log.temperature}°C</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </ProtectedShell>
  );
}
