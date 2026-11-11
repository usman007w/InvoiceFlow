import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.db import Company, PurchaseOrderRecord, SessionLocal, init_db

if len(sys.argv) != 2:
    print('Usage: python -m scripts.load_pos "Company Name"')
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
init_db()
pos = json.loads((ROOT / "purchase_orders.json").read_text())

with SessionLocal() as db:
    company = db.scalar(select(Company).where(Company.name == sys.argv[1]))
    if company is None:
        print("Company not found. Run create_admin first.")
        sys.exit(1)
    existing = {
        r.po_number
        for r in db.scalars(
            select(PurchaseOrderRecord).where(PurchaseOrderRecord.company_id == company.id)
        )
    }
    added = 0
    for po in pos:
        if po["po_number"] not in existing:
            db.add(
                PurchaseOrderRecord(
                    company_id=company.id,
                    po_number=po["po_number"],
                    data_json=json.dumps(po),
                )
            )
            added += 1
    db.commit()
print(f"Added {added} purchase orders")