import sys

from app.db import InvoiceRecord, SessionLocal

invoice_id = int(sys.argv[1])
status = sys.argv[2]

with SessionLocal() as db:
    rec = db.get(InvoiceRecord, invoice_id)
    if rec is None:
        print("No invoice with that ID")
    else:
        rec.status = status
        rec.issues_json = '["extraction_failed"]' if status == "extraction_failed" else "[]"
        db.commit()
        print(f"Invoice {invoice_id} set to {status}")