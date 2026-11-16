"use client";

import { DragEvent, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import type { Invoice } from "@/lib/types";

const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED = ["application/pdf", "image/png", "image/jpeg"];

type Item = {
  id: number;
  name: string;
  state: "queued" | "uploading" | "done" | "error";
  message?: string;
  result?: Invoice;
};

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const chain = useRef<Promise<void>>(Promise.resolve());
  const nextId = useRef(1);
  const [items, setItems] = useState<Item[]>([]);
  const [dragging, setDragging] = useState(false);

  function patch(id: number, changes: Partial<Item>) {
    setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...changes } : it)));
  }

  async function uploadOne(file: File, id: number) {
    patch(id, { state: "uploading" });
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/invoices", { method: "POST", body });
      if (res.status === 401) {
        router.replace("/login");
        return;
      }
      if (res.status === 201) {
        const result: Invoice = await res.json();
        patch(id, { state: "done", result });
        return;
      }
      const data = await res.json().catch(() => null);
      let message = typeof data?.detail === "string" ? data.detail : "Upload failed.";
      if (res.status === 403) message = "Your role is not allowed to upload invoices.";
      patch(id, { state: "error", message });
    } catch {
      patch(id, { state: "error", message: "Cannot reach the server." });
    }
  }

  function addFiles(list: FileList | File[]) {
    const files = Array.from(list);
    const fresh: Item[] = [];
    for (const file of files) {
      const id = nextId.current++;
      if (!ALLOWED.includes(file.type)) {
        fresh.push({ id, name: file.name, state: "error", message: "Only PDF, PNG and JPG files." });
        continue;
      }
      if (file.size > MAX_BYTES) {
        fresh.push({ id, name: file.name, state: "error", message: "File is larger than 10 MB." });
        continue;
      }
      fresh.push({ id, name: file.name, state: "queued" });
      chain.current = chain.current.then(() => uploadOne(file, id));
    }
    if (fresh.length > 0) {
      setItems((prev) => [...fresh, ...prev]);
      if (fresh.some((f) => f.state === "queued")) {
        chain.current = chain.current.then(() => {
          toast.success("Uploads finished");
        });
      }
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload</h1>
          <p className="mt-1 text-muted-foreground">
            Add invoices as PNG, JPG or text PDF files, up to 10 MB each.
          </p>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-12 text-center backdrop-blur-md transition-colors ${
            dragging
              ? "border-primary bg-accent"
              : "border-border bg-card/80 hover:border-primary"
          }`}
        >
          <UploadCloud className="h-10 w-10 text-primary" />
          <p className="mt-3 font-semibold">Drop invoices here or click to browse</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Each invoice takes about 10 seconds to read.
          </p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        {items.length > 0 && (
          <div className="space-y-3">
            {items.map((it) => (
              <div
                key={it.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-md border bg-card/80 px-4 py-3 backdrop-blur-md"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{it.name}</p>
                  {it.state === "queued" && (
                    <p className="text-sm text-muted-foreground">Waiting...</p>
                  )}
                  {it.state === "uploading" && (
                    <p className="animate-pulse text-sm text-primary">Reading the invoice...</p>
                  )}
                  {it.state === "error" && (
                    <p className="text-sm text-red-500">{it.message}</p>
                  )}
                  {it.state === "done" && it.result && (
                    <p className="text-sm text-muted-foreground">
                      {it.result.invoice_number ?? "No number"} · {it.result.supplier_name ?? "Unknown supplier"}
                      {it.result.issues.length > 0 && ` · ${it.result.issues.length} issue(s)`}
                    </p>
                  )}
                </div>
                {it.state === "done" && it.result && <StatusBadge status={it.result.status} />}
              </div>
            ))}
                       <Link
              href="/invoices"
              className="inline-flex cursor-pointer items-center rounded-md border bg-background/70 px-4 py-2 text-sm font-semibold backdrop-blur-md transition-colors hover:border-primary hover:text-primary"
            >
              View all invoices
            </Link>
          </div>
        )}
      </div>
    </AppShell>
  );
}