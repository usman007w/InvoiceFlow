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
## Results (synthetic scanned set, 65 invoices)

| Stage | Line items correct |
|---|---|
| Regex baseline on scans | 0/65 |
| OCR + LLM, raw | 45/65 |
| OCR + LLM + math check and repair | 65/65 |

Silent errors (wrong and not flagged): 0. Note: synthetic, clean data. Real invoices will be harder.

## Stack
FastAPI, PyMuPDF, Tesseract/PaddleOCR, LLM (Groq), PostgreSQL, Next.js, Docker

## Status
- [x] Backend skeleton and invoice schema
- [x] Synthetic invoice generator with injected errors and ground truth
- [x] Baseline extractor and evaluation
- [x] OCR for scanned invoices
- [x] LLM extraction
- [ ] Reconciliation
- [ ] Auth, roles, audit log
- [ ] Next.js frontend
- [ ] Chat agent