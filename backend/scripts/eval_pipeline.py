import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from app.extract.llm import extract_invoice
from app.extract.ocr import read_image_text
from app.extract.schemas import Invoice
from app.validate.checks import check_lines, repair_lines

limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
CACHE = ROOT / "llm_cache.json"
truth = json.loads((ROOT / "ground_truth.json").read_text())
if limit:
    truth = truth[:limit]
cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}


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


evaluated = raw_ok = final_ok = repaired_n = flagged = silent = 0
failed = []

for row in truth:
    name = row["file"]
    if name not in cache:
        try:
            text = read_image_text(ROOT / "scanned" / (Path(name).stem + ".png"))
            cache[name] = extract_invoice(text).model_dump(mode="json")
            CACHE.write_text(json.dumps(cache))
            time.sleep(2)
        except Exception as e:
            failed.append((name, str(e)[:100]))
            continue
    expected_items = row["invoice"]["line_items"]
    inv = Invoice.model_validate(cache[name])
    evaluated += 1
    raw = items_match(inv.model_dump(mode="json")["line_items"], expected_items)
    raw_ok += raw
    if repair_lines(inv):
        repaired_n += 1
    is_flagged = bool(check_lines(inv))
    final = items_match(inv.model_dump(mode="json")["line_items"], expected_items)
    final_ok += final
    flagged += is_flagged
    if not final and not is_flagged:
        silent += 1
        print("SILENT ERROR", name)

print(f"Evaluated: {evaluated}  Model failures: {len(failed)}")
print(f"Line items correct (raw LLM):     {raw_ok}/{evaluated}")
print(f"Repaired by math check:           {repaired_n}")
print(f"Line items correct (after check): {final_ok}/{evaluated}")
print(f"Flagged for human review:         {flagged}")
print(f"Silent errors (wrong, not flagged): {silent}")
for name, err in failed:
    print("FAILED", name, err)