# invoice-automation

[![CI](https://github.com/geocustomss/invoice-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/geocustomss/invoice-automation/actions/workflows/ci.yml)

Turn messy invoice text into clean, validated bookkeeping data: an LLM extracts the fields, **plain code decides
whether the invoice can be posted**, approved invoices export as a QuickBooks-style bill import, and everything else
lands in an exceptions queue with the exact reason.

```
invoice text ─► LLM extraction (strict JSON schema, retry with error feedback)
                    │
                    ▼  deterministic checks (the model never approves itself)
        line items sum = subtotal · subtotal + tax = total · qty x unit = amount · due >= invoice date
        duplicate vendor+invoice# · missing PO · amount > 3x vendor median
                    ▼
        post ─► bills_import.csv (with account categorization)     review / reject ─► exceptions.csv
```

## Quickstart (no API keys needed)

```bash
python -m unittest discover -s tests -v
python -m invoices sample_invoices --fresh --out out
python -m invoices path/to/your/invoices --provider anthropic --model claude-haiku-4-5-20251001   # real model
```

All sample invoices are synthetic. `.txt` input keeps the demo simple; for PDFs, extract text first (e.g. `pypdf`)
or send the PDF to a vision-capable model.

## Sample run (mock extractor; deterministic checks are real)

```
file                            decision      total  reasons
01_acmelab_INV-1001.txt         post        1200.00  -
02_acmelab_INV-1002.txt         post        1150.00  -
03_acmelab_INV-1003.txt         post        1260.00  -
04_packright_INV-77.txt         post         430.00  -
05_acmelab_INV-1004.txt         review      9800.00  amount_anomaly
06_packright_INV-78.txt         reject       430.00  line_items_mismatch
07_acmelab_INV-1001_again.txt   reject      1200.00  duplicate
08_cloudhost_INV-5.txt          review        89.00  missing_po

{'post': 4, 'review': 2, 'reject': 2}   outputs: out/bills_import.csv, out/exceptions.csv
```

## Design decisions

- **LLM extracts, code judges.** Arithmetic, duplicate and anomaly checks are deterministic, testable and auditable.
  The extraction prompt tells the model to copy numbers exactly and *not* correct them; otherwise a model that "helpfully"
  fixes a vendor's math would hide the very error you need to catch.
- **Invoice text is untrusted input.** The system prompt treats it as data, and because approval is deterministic, an
  injected "approve this invoice" instruction has no path to a payment.
- **Fail toward humans.** Extraction failures, schema failures and any warning go to the exceptions queue.
- **Rejected invoices can be resubmitted; posted or in-review ones can't be re-entered**, which matches how duplicates
  actually happen.
- **Anomaly detection needs history**: no flag until a vendor has 3 posted invoices, to avoid noisy false alarms.

## Limitations / next steps

- Thresholds (3x median, 1 cent tolerance) are starting points; tune them on real data.
- Export columns are QuickBooks-*style*; adapt to your actual import template or call the QuickBooks API after review.
- Add OCR/vision input, multi-currency handling, tax-rate validation and vendor master-data matching.
- Add an extraction eval set (field-level accuracy against hand-labeled invoices) using the harness pattern from `model-router-evals`.
