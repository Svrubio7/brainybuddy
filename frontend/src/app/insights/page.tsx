"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function InsightsPage() {
  const { data: weekly } = useQuery({
    queryKey: ["insights-weekly"],
    queryFn: () =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123"}/api/insights/weekly`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      }).then((r) => r.json()),
  });

  const { data: risks } = useQuery({
    queryKey: ["insights-risks"],
    queryFn: () =>
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123"}/api/insights/risk-scores`,
        { headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` } }
      ).then((r) => r.json()),
  });

  const { data: loadCurve } = useQuery({
    queryKey: ["insights-load"],
    queryFn: () =>
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123"}/api/insights/load-curve`,
        { headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` } }
      ).then((r) => r.json()),
  });

  const { data: multipliers } = useQuery({
    queryKey: ["insights-multipliers"],
    queryFn: () =>
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123"}/api/insights/multipliers`,
        { headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` } }
      ).then((r) => r.json()),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Insights</h1>

      {/* Weekly summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Planned Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{weekly?.planned_hours ?? 0}h</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Actual Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{weekly?.actual_hours ?? 0}h</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {((weekly?.completion_rate ?? 0) * 100).toFixed(0)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Risk scores */}
      <Card>
        <CardHeader>
          <CardTitle>Deadline Risk Scores</CardTitle>
        </CardHeader>
        <CardContent>
          {!risks?.length ? (
            <p className="text-[var(--muted-foreground)]">No active tasks to assess</p>
          ) : (
            <div className="space-y-2">
              {(risks as Array<{ task_id: number; task_title: string; risk_score: number; remaining_hours: number; hours_until_due: number }>).map(
                (r) => (
                  <div key={r.task_id} className="flex items-center justify-between">
                    <span className="font-medium">{r.task_title}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[var(--muted-foreground)]">
                        {r.remaining_hours}h left / {Math.round(r.hours_until_due)}h until due
                      </span>
                      <Badge
                        variant={r.risk_score > 0.7 ? "destructive" : r.risk_score > 0.4 ? "default" : "secondary"}
                      >
                        {(r.risk_score * 100).toFixed(0)}% risk
                      </Badge>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Load curve */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Load (next 14 days)</CardTitle>
        </CardHeader>
        <CardContent>
          {!loadCurve?.length ? (
            <p className="text-[var(--muted-foreground)]">No scheduled blocks</p>
          ) : (
            <div className="flex items-end gap-1 h-40">
              {(loadCurve as Array<{ date: string; planned_hours: number }>).map((d) => (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className="w-full bg-[var(--primary)] rounded-t"
                    style={{ height: `${Math.min(d.planned_hours * 15, 120)}px` }}
                    title={`${d.date}: ${d.planned_hours}h`}
                  />
                  <span className="text-[10px] text-[var(--muted-foreground)]">
                    {d.date.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Estimation multipliers */}
      <Card>
        <CardHeader>
          <CardTitle>Estimation Accuracy</CardTitle>
        </CardHeader>
        <CardContent>
          {!multipliers?.length ? (
            <p className="text-[var(--muted-foreground)]">
              Complete some tasks with time logging to see estimation patterns
            </p>
          ) : (
            <div className="space-y-2">
              {(multipliers as Array<{ course_id: number; task_type: string; multiplier: number; sample_count: number }>).map(
                (m, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span>
                      Course #{m.course_id ?? "General"} / {m.task_type}
                    </span>
                    <div className="flex items-center gap-2">
                      <Badge variant={m.multiplier > 1.3 ? "destructive" : "secondary"}>
                        {m.multiplier}x
                      </Badge>
                      <span className="text-xs text-[var(--muted-foreground)]">
                        ({m.sample_count} samples)
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
