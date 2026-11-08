import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from app.extract.llm import extract_invoice
from app.extract.ocr import read_image_text

limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
truth = json.loads((ROOT / "ground_truth.json").read_text())
if limit:
    truth = truth[:limit]

FIELDS = ["supplier_name", "invoice_number", "invoice_date", "po_number", "subtotal", "tax", "total"]
MONEY = {"subtotal", "tax", "total"}


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


correct = {f: 0 for f in FIELDS + ["line_items"]}
fully = 0
failed = []
started = time.time()

for row in truth:
    expected = row["invoice"]
    path = ROOT / "scanned" / (Path(row["file"]).stem + ".png")
    try:
        got = extract_invoice(read_image_text(path)).model_dump(mode="json")
    except Exception as e:
        failed.append((row["file"], str(e)[:80]))
        continue
    ok = {}
    for f in FIELDS:
        ok[f] = same_money(got[f], expected[f]) if f in MONEY else got[f] == expected[f]
    ok["line_items"] = items_match(got["line_items"], expected["line_items"])
    for f, v in ok.items():
        correct[f] += v
    if all(ok.values()):
        fully += 1
    else:
        print("MISS", row["file"], [f for f, v in ok.items() if not v])
    time.sleep(2)

n = len(truth)
print(f"Invoices: {n}  Model failures: {len(failed)}")
for f, c in correct.items():
    print(f"{f:16s} {c}/{n}  {100 * c / n:.1f}%")
print(f"Fully correct: {fully}/{n}  {100 * fully / n:.1f}%")
print(f"Seconds per invoice: {(time.time() - started) / n:.1f}")
for name, err in failed[:5]:
    print("FAILED", name, err)