import json
from decimal import Decimal
from pathlib import Path

from app.extract.baseline import parse_invoice
from app.extract.pdf_text import read_pdf_text

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
truth = json.loads((ROOT / "ground_truth.json").read_text())

TEXT_FIELDS = ["supplier_name", "invoice_number", "invoice_date", "po_number"]
MONEY_FIELDS = ["subtotal", "tax", "total"]


def same_money(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except Exception:
        return False


def items_match(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x["description"] != y["description"]:
            return False
        for k in ("quantity", "unit_price", "total"):
            if not same_money(x[k], y[k]):
                return False
    return True


correct = {f: 0 for f in TEXT_FIELDS + MONEY_FIELDS + ["line_items"]}
fully = 0
failures = []

for row in truth:
    expected = row["invoice"]
    got = parse_invoice(read_pdf_text(ROOT / "invoices" / row["file"]))
    ok = {}
    for f in TEXT_FIELDS:
        ok[f] = got[f] == expected[f]
    for f in MONEY_FIELDS:
        ok[f] = same_money(got[f], expected[f])
    ok["line_items"] = items_match(got["line_items"], expected["line_items"])
    for f, v in ok.items():
        correct[f] += v
    if all(ok.values()):
        fully += 1
    else:
        failures.append((row["file"], [f for f, v in ok.items() if not v]))

n = len(truth)
print(f"Invoices: {n}")
for f, c in correct.items():
    print(f"{f:16s} {c}/{n}  {100 * c / n:.1f}%")
print(f"Fully correct: {fully}/{n}  {100 * fully / n:.1f}%")
for name, bad in failures[:10]:
    print("FAIL", name, bad)