from datetime import date
from decimal import Decimal

from app.extract.schemas import Invoice, LineItem
from app.validate.checks import check_lines, check_totals, repair_lines


def make_invoice(quantity="8", line_total="191.12", total="210.23"):
    return Invoice(
        supplier_name="Test Co",
        invoice_number="INV-1",
        invoice_date=date(2026, 1, 1),
        line_items=[
            LineItem(
                description="Item",
                quantity=Decimal(quantity),
                unit_price=Decimal("23.89"),
                total=Decimal(line_total),
            )
        ],
        subtotal=Decimal("191.12"),
        tax=Decimal("19.11"),
        total=Decimal(total),
        po_number="PO-1",
    )


def test_clean_invoice_has_no_issues():
    inv = make_invoice()
    assert check_lines(inv) == []
    assert check_totals(inv) == []


def test_missing_quantity_is_repaired_from_totals():
    inv = make_invoice(quantity="19")
    assert check_lines(inv) != []
    assert repair_lines(inv) == [0]
    assert inv.line_items[0].quantity == Decimal("8")
    assert check_lines(inv) == []


def test_unrepairable_line_stays_flagged():
    inv = make_invoice(quantity="3", line_total="200.00")
    assert repair_lines(inv) == []
    assert check_lines(inv) != []


def test_wrong_document_total_is_flagged():
    inv = make_invoice(total="220.23")
    assert "total_mismatch" in check_totals(inv)