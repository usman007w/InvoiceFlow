from decimal import Decimal


def _norm(s):
    return " ".join(str(s).lower().split())


def compare_to_po(inv, po):
    if po is None:
        return ["po_not_found"]
    issues = []
    if _norm(inv.supplier_name) != _norm(po["supplier_name"]):
        issues.append("supplier_mismatch")
    remaining = [dict(it) for it in po["line_items"]]
    for it in inv.line_items:
        same = [p for p in remaining if _norm(p["description"]) == _norm(it.description)]
        if not same:
            issues.append(f"item_not_in_po:{it.description}")
            continue
        exact = next(
            (p for p in same
             if Decimal(str(p["unit_price"])) == it.unit_price
             and Decimal(str(p["quantity"])) == it.quantity),
            None,
        )
        chosen = exact or same[0]
        remaining.remove(chosen)
        if Decimal(str(chosen["unit_price"])) != it.unit_price:
            issues.append("price_mismatch")
        if Decimal(str(chosen["quantity"])) != it.quantity:
            issues.append("quantity_mismatch")
    if remaining:
        issues.append("po_items_not_invoiced")
    return list(dict.fromkeys(issues))


class DuplicateDetector:
    def __init__(self):
        self.numbers = set()
        self.contents = set()

    def check(self, inv):
        by_number = (_norm(inv.supplier_name), _norm(inv.invoice_number))
        by_content = (_norm(inv.supplier_name), str(inv.invoice_date), inv.total)
        duplicate = by_number in self.numbers or by_content in self.contents
        self.numbers.add(by_number)
        self.contents.add(by_content)
        return duplicate