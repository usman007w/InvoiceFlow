import { Badge } from "@/components/ui/badge";

const STYLES: Record<string, { label: string; className: string }> = {
  ok: {
    label: "OK",
    className: "bg-green-500/15 text-green-700 dark:text-green-400",
  },
  needs_review: {
    label: "Needs review",
    className: "bg-amber-500/15 text-amber-700 dark:text-amber-400",
  },
  approved: {
    label: "Approved",
    className: "bg-blue-500/15 text-blue-700 dark:text-blue-400",
  },
  extraction_failed: {
    label: "Failed",
    className: "bg-red-500/15 text-red-700 dark:text-red-400",
  },
};

export function StatusBadge({ status }: { status: string }) {
  const style = STYLES[status] ?? { label: status, className: "" };
  return (
    <Badge variant="secondary" className={`border-0 font-semibold ${style.className}`}>
      {style.label}
    </Badge>
  );
}