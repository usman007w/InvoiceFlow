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
- [x] OCR for scanned invoices (Tesseract)
- [x] LLM extraction (Groq) with schema validation
- [x] Validation layer (line math check, auto-repair, review flags)
- [x] End-to-end pipeline evaluation
- [x] Reconciliation (PO matching, duplicate detection)
- [x] API and database (upload, list, review, approve)
- [x] Unit tests (11 passing)
- [x] CI with GitHub Actions
- [ ] Auth, roles, audit log
- [ ] Next.js frontend
- [ ] Chat agent
- [ ] Docker and deployment

## Results (synthetic scanned set, 65 invoices)

| Stage | Line items correct |
|---|---|
| Regex baseline on scans | 0/65 |
| OCR + LLM, raw | 45/65 |
| OCR + LLM + math check and repair | 65/65 |

Silent errors (wrong and not flagged): 0. Note: synthetic, clean data. Real invoices will be harder.

## Results (synthetic scanned set, 65 invoices)

| Stage | Result |
|---|---|
| Regex baseline on scanned images | 0/65 |
| OCR + LLM, raw line items | 45/65 |
| OCR + LLM + math check and repair | 65/65 |
| Header fields (end to end) | 65/65 |
| Wrong totals on the document caught | 8/8 |
| Silent errors (wrong and not flagged) | 0 |

Note: synthetic, clean data with mild scan noise. Real invoices will be harder, and a harder test set is planned.
## Reconciliation
| Price mismatch vs purchase order caught | 6/6 |
| Duplicate invoices caught | 5/5 |
| Clean invoices falsely flagged | 0/46 |

API tested manually: upload, duplicate detection, rejection of a fake PDF (415), list/detail, approve.
## CI

[![CI](https://github.com/usman007w/InvoiceFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/usman007w/InvoiceFlow/actions/workflows/ci.yml)