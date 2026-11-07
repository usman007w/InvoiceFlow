import json
import random
from decimal import Decimal
from pathlib import Path

from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

fake = Faker()
Faker.seed(42)
random.seed(42)

OUT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
PDF_DIR = OUT / "invoices"
PDF_DIR.mkdir(parents=True, exist_ok=True)

SUPPLIERS = [fake.company() for _ in range(8)]
PRODUCTS = ["Laptop stand", "USB-C cable", "Office chair", "Printer paper",
            "Monitor", "Keyboard", "Desk lamp", "Webcam"]
TAX_RATE = Decimal("0.10")


def money(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))


def build_totals(inv):
    for it in inv["line_items"]:
        it["total"] = str(money(Decimal(it["quantity"]) * Decimal(it["unit_price"])))
    subtotal = sum(Decimal(it["total"]) for it in inv["line_items"])
    tax = money(subtotal * TAX_RATE)
    inv["subtotal"] = str(subtotal)
    inv["tax"] = str(tax)
    inv["total"] = str(subtotal + tax)


def make_po(i):
    items = []
    for _ in range(random.randint(1, 4)):
        items.append({
            "description": random.choice(PRODUCTS),
            "quantity": random.randint(1, 20),
            "unit_price": str(money(round(random.uniform(5, 300), 2))),
            "total": "0",
        })
    po = {
        "po_number": f"PO-{1000 + i}",
        "supplier_name": random.choice(SUPPLIERS),
        "line_items": items,
    }
    build_totals(po)
    return po


def make_invoice(po, i):
    inv = {
        "supplier_name": po["supplier_name"],
        "invoice_number": f"INV-{5000 + i}",
        "invoice_date": str(fake.date_between(start_date="-120d", end_date="today")),
        "currency": "USD",
        "po_number": po["po_number"],
        "line_items": [dict(it) for it in po["line_items"]],
    }
    build_totals(inv)
    return inv


def draw_pdf(path, inv):
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, inv["supplier_name"])
    y -= 30
    c.setFont("Helvetica", 11)
    for label, key in [("Invoice No", "invoice_number"), ("Date", "invoice_date"),
                       ("PO Number", "po_number")]:
        c.drawString(50, y, f"{label}: {inv[key]}")
        y -= 18
    y -= 15
    for x, h in [(50, "Description"), (300, "Qty"), (360, "Unit price"), (450, "Total")]:
        c.drawString(x, y, h)
    y -= 18
    for it in inv["line_items"]:
        c.drawString(50, y, it["description"])
        c.drawString(300, y, str(it["quantity"]))
        c.drawString(360, y, it["unit_price"])
        c.drawString(450, y, it["total"])
        y -= 18
    y -= 15
    c.drawString(360, y, f"Subtotal: {inv['subtotal']}")
    y -= 18
    c.drawString(360, y, f"Tax: {inv['tax']}")
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(360, y, f"Total: {inv['total']} {inv['currency']}")
    c.save()


def main(n=60):
    pos, truth = [], []
    for i in range(n):
        po = make_po(i)
        pos.append(po)
        inv = make_invoice(po, i)
        roll = random.random()
        error = "none"
        if roll < 0.10:
            error = "wrong_total"
            inv["total"] = str(Decimal(inv["total"]) + Decimal("10.00"))
        elif roll < 0.20:
            error = "price_mismatch"
            inv["line_items"][0]["unit_price"] = str(
                money(Decimal(inv["line_items"][0]["unit_price"]) * Decimal("1.15")))
            build_totals(inv)
        name = f"invoice_{i:03d}.pdf"
        draw_pdf(PDF_DIR / name, inv)
        truth.append({"file": name, "error": error, "invoice": inv})
        if random.random() < 0.08:
            dup_name = f"invoice_{i:03d}_dup.pdf"
            draw_pdf(PDF_DIR / dup_name, inv)
            truth.append({"file": dup_name, "error": "duplicate", "invoice": inv})
    (OUT / "purchase_orders.json").write_text(json.dumps(pos, indent=2))
    (OUT / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    print(f"Created {len(truth)} invoices and {len(pos)} purchase orders in {OUT}")


if __name__ == "__main__":
    main()