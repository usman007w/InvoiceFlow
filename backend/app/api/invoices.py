import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.audit import log_event
from app.core.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.db import InvoiceRecord, PurchaseOrderRecord, User, get_db, utcnow
from app.extract.llm import extract_invoice
from app.extract.schemas import Invoice
from app.pipeline import full_check, read_text
from app.validate.reconcile import DuplicateDetector

router = APIRouter(prefix="/invoices", tags=["invoices"])

WRITERS = ("admin", "reviewer")

SIGNATURES = [
    (b"%PDF", ".pdf"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
]


def detect_type(head):
    for signature, ext in SIGNATURES:
        if head.startswith(signature):
            return ext
    return None


def build_context(db, company_id, before_id=None):
    pos_index = {}
    pos = select(PurchaseOrderRecord).where(PurchaseOrderRecord.company_id == company_id)
    for po in db.scalars(pos):
        pos_index[po.po_number] = json.loads(po.data_json)
    detector = DuplicateDetector()
    query = (
        select(InvoiceRecord)
        .where(InvoiceRecord.company_id == company_id)
        .order_by(InvoiceRecord.id)
    )
    for rec in db.scalars(query):
        if before_id is not None and rec.id >= before_id:
            continue
        if rec.data_json:
            detector.check(Invoice.model_validate_json(rec.data_json))
    return pos_index, detector


def get_owned(db, invoice_id, user):
    rec = db.scalar(
        select(InvoiceRecord).where(
            InvoiceRecord.id == invoice_id,
            InvoiceRecord.company_id == user.company_id,
        )
    )
    if rec is None:
        raise HTTPException(404, "Invoice not found")
    return rec


def to_dict(rec, detail=False):
    data = json.loads(rec.data_json) if rec.data_json else None
    out = {
        "id": rec.id,
        "original_name": rec.original_name,
        "status": rec.status,
        "issues": json.loads(rec.issues_json),
        "repaired_lines": json.loads(rec.repaired_json),
        "supplier_name": data["supplier_name"] if data else None,
        "invoice_number": data["invoice_number"] if data else None,
        "total": data["total"] if data else None,
        "created_at": rec.created_at.isoformat(),
    }
    if detail:
        out["data"] = data
    return out


@router.post("", status_code=201)
def upload_invoice(
    request: Request,
    file: UploadFile,
    user: User = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
):
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (10 MB max)")
    ext = detect_type(content[:8])
    if ext is None:
        raise HTTPException(415, "Only PDF, PNG and JPG files are allowed")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(content)
    original = (file.filename or "upload")[:200]

    try:
        inv = extract_invoice(read_text(path))
    except ValueError as e:
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(e))
    except Exception:
        rec = InvoiceRecord(
            company_id=user.company_id,
            uploaded_by=user.id,
            original_name=original,
            stored_name=stored_name,
            status="extraction_failed",
            issues_json=json.dumps(["extraction_failed"]),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        log_event(db, "invoice_upload_failed", user=user, target=f"invoice:{rec.id}", request=request)
        return to_dict(rec)

    pos_index, detector = build_context(db, user.company_id)
    result = full_check(inv, pos_index, detector)
    rec = InvoiceRecord(
        company_id=user.company_id,
        uploaded_by=user.id,
        original_name=original,
        stored_name=stored_name,
        status=result["status"],
        data_json=result["invoice"].model_dump_json(),
        issues_json=json.dumps(result["issues"]),
        repaired_json=json.dumps(result["repaired"]),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    log_event(
        db, "invoice_upload", user=user, target=f"invoice:{rec.id}",
        detail={"status": rec.status, "issues": result["issues"]}, request=request,
    )
    return to_dict(rec, detail=True)


@router.get("")
def list_invoices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.scalars(
        select(InvoiceRecord)
        .where(InvoiceRecord.company_id == user.company_id)
        .order_by(InvoiceRecord.id.desc())
    )
    return [to_dict(r) for r in records]


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return to_dict(get_owned(db, invoice_id, user), detail=True)


class InvoiceUpdate(BaseModel):
    data: Invoice | None = None
    approve: bool = False


@router.patch("/{invoice_id}")
def update_invoice(
    invoice_id: int,
    body: InvoiceUpdate,
    request: Request,
    user: User = Depends(require_roles(*WRITERS)),
    db: Session = Depends(get_db),
):
    rec = get_owned(db, invoice_id, user)
    if body.data is None and not rec.data_json:
        raise HTTPException(422, "This invoice has no extracted data. Send the corrected fields.")
    inv = body.data or Invoice.model_validate_json(rec.data_json)

    pos_index, detector = build_context(db, user.company_id, before_id=rec.id)
    result = full_check(inv, pos_index, detector)
    rec.data_json = result["invoice"].model_dump_json()
    rec.issues_json = json.dumps(result["issues"])
    rec.repaired_json = json.dumps(result["repaired"])
    if body.approve:
        rec.status = "approved"
        rec.reviewed_at = utcnow()
    else:
        rec.status = result["status"]
    db.commit()
    db.refresh(rec)
    log_event(
        db,
        "invoice_approved" if body.approve else "invoice_edited",
        user=user,
        target=f"invoice:{rec.id}",
        detail={"issues": result["issues"], "fields_edited": body.data is not None},
        request=request,
    )
    return to_dict(rec, detail=True)