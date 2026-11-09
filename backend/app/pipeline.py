from pathlib import Path

from app.extract.llm import extract_invoice
from app.extract.ocr import read_image_text
from app.extract.pdf_text import read_pdf_text
from app.validate.checks import check_lines, check_totals, repair_lines


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


def process_file(path):
    return validate_invoice(extract_invoice(read_text(path)))