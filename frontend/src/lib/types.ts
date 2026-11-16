export type Invoice = {
  id: number;
  original_name: string;
  status: string;
  issues: string[];
  repaired_lines: number[];
  supplier_name: string | null;
  invoice_number: string | null;
  total: string | null;
  created_at: string;
};