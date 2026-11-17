"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { StatusBadge } from "@/components/status-badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Invoice } from "@/lib/types";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "needs_review", label: "Needs review" },
  { key: "ok", label: "OK" },
  { key: "approved", label: "Approved" },
  { key: "extraction_failed", label: "Failed" },
];

function money(value: string | null) {
  if (value === null) return "-";
  const n = Number(value);
  if (!Number.isFinite(n)) return value;
  return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function when(value: string) {
  const d = new Date(value.endsWith("Z") ? value : value + "Z");
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function issueText(issues: string[]) {
  if (issues.length === 0) return "None";
  const names = Array.from(new Set(issues.map((i) => i.replace(/:.*/, "").replace(/_/g, " "))));
  const shown = names.slice(0, 2).join(", ");
  return names.length > 2 ? `${shown} +${names.length - 2}` : shown;
}

export default function InvoicesPage() {
  const router = useRouter();
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch("/api/invoices")
      .then(async (res) => {
        if (res.status === 401) {
          router.replace("/login");
          return;
        }
        if (!res.ok) throw new Error("failed");
        setInvoices(await res.json());
      })
      .catch(() => setError("Could not load invoices. Is the backend running?"));
  }, [router]);

  const counts = useMemo(() => {
    const result: Record<string, number> = { all: invoices?.length ?? 0 };
    for (const inv of invoices ?? []) {
      result[inv.status] = (result[inv.status] ?? 0) + 1;
    }
    return result;
  }, [invoices]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (invoices ?? []).filter((inv) => {
      if (filter !== "all" && inv.status !== filter) return false;
      if (!q) return true;
      return [inv.supplier_name, inv.invoice_number, inv.original_name]
        .filter(Boolean)
        .some((text) => String(text).toLowerCase().includes(q));
    });
  }, [invoices, filter, query]);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Invoices</h1>
          <p className="mt-1 text-muted-foreground">
            Extracted, checked and ready for review.
          </p>
        </div>

        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500 dark:text-zinc-400" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search supplier, invoice number or file name"
            className="h-11 bg-background/70 pl-9 shadow-sm backdrop-blur-md"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={
                filter === f.key
                  ? "cursor-pointer rounded-md bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground transition-colors"
                  : "cursor-pointer rounded-md border bg-background/70 px-3 py-1.5 text-sm text-muted-foreground backdrop-blur-md transition-colors hover:text-foreground"
              }
            >
              {f.label} <span className="opacity-70">{counts[f.key] ?? 0}</span>
            </button>
          ))}
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        {!error && invoices === null && (
          <div className="space-y-3">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />
            ))}
          </div>
        )}

        {invoices !== null && visible.length === 0 && (
          <div className="rounded-md border bg-card/80 p-10 text-center backdrop-blur-md">
            <p className="font-semibold">
              {invoices.length === 0 ? "No invoices yet" : "No invoices match"}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {invoices.length === 0
                ? "Uploads will appear here. The upload page comes in the next step."
                : "Try a different search or filter."}
            </p>
          </div>
        )}

        {invoices !== null && visible.length > 0 && (
          <div className="overflow-x-auto rounded-md border bg-card/80 shadow-sm backdrop-blur-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice</TableHead>
                  <TableHead>Supplier</TableHead>
                  <TableHead className="pr-8 text-right">Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Issues</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((inv) => (
                  <TableRow key={inv.id} className="transition-colors hover:bg-accent">
                                        <TableCell className="font-medium">
                      <Link
                        href={`/invoices/${inv.id}`}
                        className="hover:text-primary hover:underline underline-offset-4"
                      >
                        {inv.invoice_number ?? inv.original_name}
                      </Link>
                    </TableCell>
                    <TableCell>{inv.supplier_name ?? "-"}</TableCell>
                    <TableCell className="pr-8 text-right tabular-nums">
                      {money(inv.total)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={inv.status} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {issueText(inv.issues)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {when(inv.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </AppShell>
  );
}