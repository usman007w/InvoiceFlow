import json
from pathlib import Path

from app.extract.schemas import Invoice
from app.pipeline import validate_invoice
from app.validate.compare import items_match, same_money

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
truth = json.loads((ROOT / "ground_truth.json").read_text())
cache = json.loads((ROOT / "llm_cache.json").read_text())

FIELDS = ["supplier_name", "invoice_number", "invoice_date", "po_number", "subtotal", "tax", "total"]
MONEY = {"subtotal", "tax", "total"}

headers_ok = items_ok = fully = 0
by_type = {}
bad_headers = []

for row in truth:
    name = row["file"]
    if name not in cache:
        continue
    result = validate_invoice(Invoice.model_validate(cache[name]))
    got = result["invoice"].model_dump(mode="json")
    exp = row["invoice"]
    h = all(
        same_money(got[f], exp[f]) if f in MONEY else got[f] == exp[f]
        for f in FIELDS
    )
    i = items_match(got["line_items"], exp["line_items"])
    headers_ok += h
    items_ok += i
    fully += h and i
    if not h:
        bad_headers.append(name)
    t = by_type.setdefault(row["error"], {"n": 0, "flagged": 0, "total_flag": 0})
    t["n"] += 1
    t["flagged"] += result["status"] == "needs_review"
    t["total_flag"] += "total_mismatch" in result["issues"]

n = sum(t["n"] for t in by_type.values())
print(f"Invoices: {n}")
print(f"Header fields correct: {headers_ok}/{n}")
print(f"Line items correct:    {items_ok}/{n}")
print(f"Fully correct:         {fully}/{n}")
for name in bad_headers[:5]:
    print("BAD HEADER", name)
print()
for kind, t in by_type.items():
    print(f"{kind:15s} count={t['n']:3d}  flagged={t['flagged']:3d}  total_mismatch={t['total_flag']:3d}")