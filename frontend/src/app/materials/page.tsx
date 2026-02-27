"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8123";

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem("access_token")}` };
}

export default function MaterialsPage() {
  const qc = useQueryClient();
  const [dragOver, setDragOver] = useState(false);
  const [extraction, setExtraction] = useState<{
    material_id: number;
    tasks: Array<{ title: string; due_date: string; estimated_hours: number; task_type: string }>;
    events: Array<{ title: string; day_of_week: string; start_time: string; end_time: string }>;
    confidence: number;
  } | null>(null);

  const { data: materials } = useQuery({
    queryKey: ["materials"],
    queryFn: () =>
      fetch(`${API_URL}/api/materials`, { headers: authHeaders() }).then((r) => r.json()),
  });

  const uploadMut = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_URL}/api/materials/upload`, {
        method: "POST",
        headers: authHeaders(),
        body: form,
      });
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["materials"] }),
  });

  const extractMut = useMutation({
    mutationFn: async (materialId: number) => {
      const res = await fetch(`${API_URL}/api/materials/extract/${materialId}`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
      });
      return res.json();
    },
    onSuccess: (data) => {
      setExtraction({
        material_id: data.material_id,
        tasks: data.extracted_tasks,
        events: data.extracted_events,
        confidence: data.confidence,
      });
    },
  });

  const confirmMut = useMutation({
    mutationFn: async () => {
      if (!extraction) return;
      const res = await fetch(`${API_URL}/api/materials/confirm-extraction`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
          material_id: extraction.material_id,
          tasks_to_create: extraction.tasks,
          events_to_create: extraction.events,
        }),
      });
      return res.json();
    },
    onSuccess: () => {
      setExtraction(null);
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) uploadMut.mutate(file);
    },
    [uploadMut]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Materials & Ingestion</h1>

      {/* Upload zone */}
      <Card
        className={`border-2 border-dashed p-8 text-center cursor-pointer ${
          dragOver ? "border-[var(--primary)] bg-[var(--accent)]" : ""
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => {
          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg";
          input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) uploadMut.mutate(file);
          };
          input.click();
        }}
      >
        <p className="text-lg font-medium">
          {uploadMut.isPending ? "Uploading..." : "Drop a file here or click to upload"}
        </p>
        <p className="text-sm text-[var(--muted-foreground)] mt-1">
          Supports PDF, DOC, images (syllabus, assignments, timetables)
        </p>
      </Card>

      {/* Extraction preview */}
      {extraction && (
        <Card>
          <CardHeader>
            <CardTitle>
              Extraction Preview{" "}
              <Badge variant="secondary">{(extraction.confidence * 100).toFixed(0)}% confident</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {extraction.tasks.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Tasks ({extraction.tasks.length})</h3>
                <div className="space-y-1">
                  {extraction.tasks.map((t, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span>{t.title}</span>
                      <span className="text-[var(--muted-foreground)]">
                        Due: {t.due_date} | {t.estimated_hours}h | {t.task_type}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {extraction.events.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Events ({extraction.events.length})</h3>
                <div className="space-y-1">
                  {extraction.events.map((e, i) => (
                    <div key={i} className="text-sm">
                      {e.title} - {e.day_of_week} {e.start_time}-{e.end_time}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <Button onClick={() => confirmMut.mutate()} disabled={confirmMut.isPending}>
                Confirm & Create Tasks
              </Button>
              <Button variant="outline" onClick={() => setExtraction(null)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Materials list */}
      <Card>
        <CardHeader>
          <CardTitle>Uploaded Materials</CardTitle>
        </CardHeader>
        <CardContent>
          {!materials?.length ? (
            <p className="text-[var(--muted-foreground)]">No materials uploaded yet</p>
          ) : (
            <div className="space-y-2">
              {(materials as Array<{ id: number; filename: string; content_type: string; file_size: number; extraction_status: string; created_at: string }>).map(
                (m) => (
                  <div key={m.id} className="flex items-center justify-between">
                    <div>
                      <span className="font-medium">{m.filename}</span>
                      <span className="text-sm text-[var(--muted-foreground)] ml-2">
                        {(m.file_size / 1024).toFixed(1)}KB
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{m.extraction_status}</Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => extractMut.mutate(m.id)}
                        disabled={extractMut.isPending}
                      >
                        Extract
                      </Button>
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
