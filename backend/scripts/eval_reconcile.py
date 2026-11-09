import json
from pathlib import Path

from app.extract.schemas import Invoice
from app.pipeline import full_check
from app.validate.reconcile import DuplicateDetector

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
truth = json.loads((ROOT / "ground_truth.json").read_text())
cache = json.loads((ROOT / "llm_cache.json").read_text())
pos_index = {p["po_number"]: p for p in json.loads((ROOT / "purchase_orders.json").read_text())}
detector = DuplicateDetector()

EXPECT = {
    "wrong_total": "total_mismatch",
    "price_mismatch": "price_mismatch",
    "duplicate": "duplicate",
}
stats = {k: {"n": 0, "caught": 0} for k in EXPECT}
clean_n = clean_flagged = 0

for row in truth:
    name = row["file"]
    result = full_check(Invoice.model_validate(cache[name]), pos_index, detector)
    issues = result["issues"]
    label = row["error"]
    if label == "none":
        clean_n += 1
        if issues:
            clean_flagged += 1
            print("FALSE ALARM", name, issues)
    else:
        stats[label]["n"] += 1
        if EXPECT[label] in issues:
            stats[label]["caught"] += 1
        else:
            print("MISSED", label, name, issues)

print()
for label, s in stats.items():
    print(f"{label:15s} caught {s['caught']}/{s['n']}")
print(f"Clean invoices falsely flagged: {clean_flagged}/{clean_n}")