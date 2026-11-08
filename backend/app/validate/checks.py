from decimal import Decimal

CENT = Decimal("0.01")


def check_lines(invoice):
    issues = []
    for i, it in enumerate(invoice.line_items):
        if abs(it.quantity * it.unit_price - it.total) > CENT:
            issues.append(("line_math", i))
    return issues


def repair_lines(invoice):
    repaired = []
    for i, it in enumerate(invoice.line_items):
        if abs(it.quantity * it.unit_price - it.total) > CENT and it.unit_price > 0:
            q = it.total / it.unit_price
            whole = q.to_integral_value()
            if q >= 1 and abs(q - whole) < Decimal("0.005"):
                it.quantity = whole
                repaired.append(i)
    return repaired


def check_totals(invoice):
    issues = []
    subtotal = sum(it.total for it in invoice.line_items)
    if abs(subtotal - invoice.subtotal) > CENT:
        issues.append("subtotal_mismatch")
    if abs(invoice.subtotal + invoice.tax - invoice.total) > CENT:
        issues.append("total_mismatch")
    return issues