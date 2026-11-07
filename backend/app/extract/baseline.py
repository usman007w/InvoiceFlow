import re


def _find(pattern, text):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def parse_invoice(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    result = {
        "supplier_name": lines[0] if lines else None,
        "invoice_number": _find(r"Invoice No:\s*(\S+)", text),
        "invoice_date": _find(r"Date:\s*(\d{4}-\d{2}-\d{2})", text),
        "po_number": _find(r"PO Number:\s*(\S+)", text),
        "subtotal": _find(r"Subtotal:\s*([\d.]+)", text),
        "tax": _find(r"Tax:\s*([\d.]+)", text),
        "total": _find(r"Total:\s*([\d.]+)", text),
    }
    items = []
    if "Description" in lines:
        start = lines.index("Description") + 4
        end = next((i for i, l in enumerate(lines) if l.startswith("Subtotal")), len(lines))
        body = lines[start:end]
        for k in range(0, len(body) - 3, 4):
            items.append({
                "description": body[k],
                "quantity": body[k + 1],
                "unit_price": body[k + 2],
                "total": body[k + 3],
            })
    result["line_items"] = items
    return result