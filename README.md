# InvoiceFlow

AI invoice extraction, reconciliation and chat, with a security-focused design.

## Flow

```
Invoices (folder / Gmail)
        |
   Upload + validation
        |
  OCR / PDF text extraction
        |
  LLM extraction -> Pydantic schema
        |
  Validation (math, dates, tax)
        |
  Reconciliation vs purchase orders
        |
  Human review (low-confidence fields)
        |
  Database -> Excel / Google Sheets
        |
  Chat agent (read-only queries)
```

## Stack
FastAPI, PyMuPDF, Tesseract/PaddleOCR, LLM (Groq), PostgreSQL, Next.js, Docker

## Status
- [x] Backend skeleton and invoice schema
- [x] Synthetic invoice generator with injected errors and ground truth
- [x] Baseline extractor and evaluation
- [x] OCR for scanned invoices
- [ ] LLM extraction
- [ ] Reconciliation
- [ ] Auth, roles, audit log
- [ ] Next.js frontend
- [ ] Chat agent