import { AppShell } from "@/components/app-shell";

export default function InvoicesPage() {
  return (
    <AppShell>
      <h1 className="text-3xl font-bold tracking-tight">Invoices</h1>
      <p className="mt-2 text-muted-foreground">
        Your invoice list appears here in the next step.
      </p>
    </AppShell>
  );
}