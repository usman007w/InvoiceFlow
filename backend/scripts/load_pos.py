import json
from pathlib import Path

from app.db import PurchaseOrderRecord, SessionLocal, init_db

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
init_db()
pos = json.loads((ROOT / "purchase_orders.json").read_text())

added = 0
with SessionLocal() as db:
    for po in pos:
        if db.get(PurchaseOrderRecord, po["po_number"]) is None:
            db.add(PurchaseOrderRecord(po_number=po["po_number"], data_json=json.dumps(po)))
            added += 1
    db.commit()
print(f"Added {added} purchase orders")