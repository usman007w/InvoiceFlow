from tests.test_checks import make_invoice

from app.validate.reconcile import DuplicateDetector, compare_to_po


def make_po(unit_price="23.89"):
    return {
        "po_number": "PO-1",
        "supplier_name": "Test Co",
        "line_items": [
            {"description": "Item", "quantity": 8, "unit_price": unit_price, "total": "191.12"}
        ],
    }


def test_matching_po_has_no_issues():
    assert compare_to_po(make_invoice(), make_po()) == []


def test_price_difference_is_flagged():
    assert "price_mismatch" in compare_to_po(make_invoice(), make_po("20.00"))


def test_unknown_po_is_flagged():
    assert compare_to_po(make_invoice(), None) == ["po_not_found"]


def test_second_identical_invoice_is_duplicate():
    detector = DuplicateDetector()
    inv = make_invoice()
    assert detector.check(inv) is False
    assert detector.check(inv) is True