"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Invoice } from "@/lib/types";

type LineItem = { description: string; quantity: string; unit_price: string; total: string };
type Data = {
  supplier_name: string;
  invoice_number: string;
  invoice_date: string;
  currency: string;
  line_items: LineItem[];
  subtotal: string;
  tax: string;
  total: string;
  po_number: string | null;
};
type Detail = Invoice & { data: Data | null; file_type: string };

function issueLabel(issue: string) {
  return issue.replace(/:.*/, "").replace(/_/g, " ");
}

export default function ReviewPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [inv, setInv] = useState<Detail | null>(null);
  const [draft, setDraft] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(`/api/invoices/${id}`).then(async (res) => {
      if (res.status === 401) return router.replace("/login");
      if (res.status === 404) return setError("Invoice not found.");
      if (!res.ok) return setError("Could not load this invoice.");
      const data: Detail = await res.json();
      setInv(data);
      setDraft(data.data);
    });
  }, [id, router]);

  async function save(approve: boolean) {
    if (!draft) return;
    setBusy(true);
    try {
      const res = await fetch(`/api/invoices/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: draft, approve }),
      });
      if (!res.ok) {
        toast.error("Could not save. Check the fields and try again.");
        return;
      }
      const updated: Detail = await res.json();
      setInv(updated);
      setDraft(updated.data);
      toast.success(approve ? "Invoice approved" : "Changes saved");
    } finally {
      setBusy(false);
    }
  }

  function setField<K extends keyof Data>(key: K, value: Data[K]) {
    setDraft((d) => (d ? { ...d, [key]: value } : d));
  }

  function setLine(index: number, key: keyof LineItem, value: string) {
    setDraft((d) => {
      if (!d) return d;
      const lines = d.line_items.map((l, i) => (i === index ? { ...l, [key]: value } : l));
      return { ...d, line_items: lines };
    });
  }

  if (error) {
    return (
      <AppShell>
        <p className="text-red-500">{error}</p>
        <Link href="/invoices" className="mt-4 inline-block text-primary underline">
          Back to invoices
        </Link>
      </AppShell>
    );
  }

  if (!inv || !draft) {
    return (
      <AppShell>
        <div className="h-64 animate-pulse rounded-md bg-muted" />
      </AppShell>
    );
  }

  const repaired = new Set(inv.repaired_lines);
  const hasIssueText = inv.issues.some((i) => i.startsWith("line_math"));

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link href="/invoices" className="text-sm text-muted-foreground hover:text-primary">
              ← Back to invoices
            </Link>
            <h1 className="mt-1 text-3xl font-bold tracking-tight">
              {inv.invoice_number ?? inv.original_name}
            </h1>
          </div>
          <StatusBadge status={inv.status} />
        </div>

        {inv.issues.length > 0 && (
          <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-4">
            <p className="font-semibold">Needs your review</p>
            <ul className="mt-2 list-inside list-disc text-sm">
              {Array.from(new Set(inv.issues.map(issueLabel))).map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
            {hasIssueText && (
              <p className="mt-2 text-sm text-muted-foreground">
                A quantity was repaired from the line total. Check it against the document.
              </p>
            )}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="overflow-hidden rounded-md border bg-card/80 backdrop-blur-md">
            {inv.file_type === "pdf" ? (
              <iframe
                src={`/api/invoices/${id}/file`}
                title="Invoice"
                className="h-[70vh] w-full"
              />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`/api/invoices/${id}/file`}
                alt="Invoice"
                className="h-auto w-full"
              />
            )}
          </div>

          <div className="space-y-4 rounded-md border bg-card/80 p-5 backdrop-blur-md">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Supplier" value={draft.supplier_name} onChange={(v) => setField("supplier_name", v)} />
              <Field label="Invoice number" value={draft.invoice_number} onChange={(v) => setField("invoice_number", v)} />
              <Field label="Date (YYYY-MM-DD)" value={draft.invoice_date} onChange={(v) => setField("invoice_date", v)} />
              <Field label="PO number" value={draft.po_number ?? ""} onChange={(v) => setField("po_number", v || null)} />
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold">Line items</p>
              <div className="space-y-2">
                {draft.line_items.map((line, i) => (
                  <div
                    key={i}
                    className={`grid grid-cols-12 gap-2 rounded-md border p-2 ${
                      repaired.has(i) ? "border-amber-500/60 bg-amber-500/10" : ""
                    }`}
                  >
                    <Input
                      className="col-span-12 sm:col-span-4"
                      value={line.description}
                      onChange={(e) => setLine(i, "description", e.target.value)}
                    />
                    <Input
                      className="col-span-4 sm:col-span-2"
                      value={line.quantity}
                      onChange={(e) => setLine(i, "quantity", e.target.value)}
                      aria-label="Quantity"
                    />
                    <Input
                      className="col-span-4 sm:col-span-3"
                      value={line.unit_price}
                      onChange={(e) => setLine(i, "unit_price", e.target.value)}
                      aria-label="Unit price"
                    />
                    <Input
                      className="col-span-4 sm:col-span-3"
                      value={line.total}
                      onChange={(e) => setLine(i, "total", e.target.value)}
                      aria-label="Line total"
                    />
                  </div>
                ))}
              </div>
              {repaired.size > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Highlighted lines had their quantity repaired automatically.
                </p>
              )}
            </div>

            <div className="grid grid-cols-3 gap-3">
              <Field label="Subtotal" value={draft.subtotal} onChange={(v) => setField("subtotal", v)} />
              <Field label="Tax" value={draft.tax} onChange={(v) => setField("tax", v)} />
              <Field label="Total" value={draft.total} onChange={(v) => setField("total", v)} />
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Button variant="outline" disabled={busy} onClick={() => save(false)} className="cursor-pointer">
                Save changes
              </Button>
              <Button disabled={busy} onClick={() => save(true)} className="cursor-pointer font-semibold">
                Approve
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Saving re-checks the invoice. Approving marks it as reviewed and is recorded in the audit log.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string | null;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <Input value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}