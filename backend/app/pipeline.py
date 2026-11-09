from pathlib import Path

from app.extract.llm import extract_invoice
from app.extract.ocr import read_image_text
from app.extract.pdf_text import read_pdf_text
from app.validate.checks import check_lines, check_totals, repair_lines
from app.validate.reconcile import compare_to_po


def read_text(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        text = read_pdf_text(path)
        if len(text.strip()) < 20:
            raise ValueError("Scanned PDFs are not supported yet. Upload PNG or JPG.")
        return text
    return read_image_text(path)


def validate_invoice(inv):
    repaired = repair_lines(inv)
    issues = [f"line_math:{i}" for _, i in check_lines(inv)] + check_totals(inv)
    return {
        "invoice": inv,
        "repaired": repaired,
        "issues": issues,
        "status": "needs_review" if issues else "ok",
    }


def full_check(inv, pos_index, detector):
    result = validate_invoice(inv)
    invoice = result["invoice"]
    issues = list(result["issues"])
    issues += compare_to_po(invoice, pos_index.get(invoice.po_number))
    if detector.check(invoice):
        issues.append("duplicate")
    result["issues"] = issues
    result["status"] = "needs_review" if issues else "ok"
    return result


def process_file(path, pos_index, detector):
    return full_check(extract_invoice(read_text(path)), pos_index, detector)