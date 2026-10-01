import csv
import json
import os
import tempfile
import unittest

from invoices import export, ledger, llm, mock
from invoices.extract import extract_invoice, validate_schema
from invoices.pipeline import process_dir
from invoices.validate import check_invoice, decide

llm.register_mock(mock.handler)


def invoice(**kw):
    base = {"vendor": "V", "invoice_number": "1", "invoice_date": "2026-08-01", "due_date": "2026-09-01",
            "po_number": "PO-1", "currency": "USD", "subtotal": 100.0, "tax": 0.0, "total": 100.0,
            "line_items": [{"description": "Thing", "qty": 2, "unit_price": 50.0, "amount": 100.0}]}
    base.update(kw)
    return base


def codes(flags):
    return {f["code"] for f in flags}


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.db = tempfile.mktemp(suffix=".db")

    def test_clean_invoice_posts(self):
        flags = check_invoice(invoice(), self.db)
        self.assertEqual((flags, decide(flags)), ([], "post"))

    def test_math_errors_reject(self):
        flags = check_invoice(invoice(subtotal=110.0, total=110.0), self.db)
        self.assertIn("line_items_mismatch", codes(flags))
        self.assertEqual(decide(flags), "reject")
        self.assertIn("total_mismatch", codes(check_invoice(invoice(total=105.0), self.db)))
        bad_line = invoice(line_items=[{"description": "T", "qty": 2, "unit_price": 40.0, "amount": 100.0}])
        self.assertIn("line_math", codes(check_invoice(bad_line, self.db)))

    def test_dates(self):
        self.assertIn("due_before_invoice", codes(check_invoice(invoice(due_date="2026-07-01"), self.db)))

    def test_missing_po_goes_to_review(self):
        flags = check_invoice(invoice(po_number=None), self.db)
        self.assertEqual(decide(flags), "review")

    def test_duplicate_and_resubmission_rules(self):
        ledger.add(self.db, "V", "1", 100.0, "post")
        self.assertIn("duplicate", codes(check_invoice(invoice(vendor=" v ", invoice_number="1"), self.db)))
        ledger.add(self.db, "W", "9", 50.0, "reject")        # rejected invoices may be resubmitted
        self.assertNotIn("duplicate", codes(check_invoice(invoice(vendor="W", invoice_number="9"), self.db)))

    def test_amount_anomaly_needs_history(self):
        big = invoice(subtotal=1000.0, total=1000.0,
                      line_items=[{"description": "T", "qty": 1, "unit_price": 1000.0, "amount": 1000.0}])
        self.assertNotIn("amount_anomaly", codes(check_invoice(big, self.db)))
        for i, t in enumerate((90.0, 100.0, 110.0)):
            ledger.add(self.db, "V", f"H{i}", t, "post")
        self.assertIn("amount_anomaly", codes(check_invoice(big, self.db)))


class ExtractTest(unittest.TestCase):
    def test_schema_rejects_bad_data(self):
        for patch in ({"invoice_date": "08/01/2026"}, {"total": "100"}, {"line_items": []}, {"vendor": ""}):
            with self.assertRaises(ValueError):
                validate_schema(invoice(**patch))

    def test_retry_on_invalid_json_and_po_normalization(self):
        good = json.dumps(invoice(po_number="none"))
        replies = iter(["Sure! Here is the invoice:", good])
        inv, _ = extract_invoice("text", complete_fn=lambda p, **kw: llm.Completion(next(replies), "mock", "m"))
        self.assertIsNone(inv["po_number"])

    def test_prompt_tells_model_not_to_fix_math(self):
        from invoices.extract import SYSTEM
        self.assertIn("do not fix", SYSTEM)


class ExportTest(unittest.TestCase):
    def test_categorize(self):
        self.assertEqual(export.categorize("Lab reagents kit"), "Lab Supplies")
        self.assertEqual(export.categorize("Mystery"), "Uncategorized Expense")

    def test_write_bills_rows(self):
        path = tempfile.mktemp(suffix=".csv")
        self.assertEqual(export.write_bills(path, [invoice(), invoice()]), 2)
        with open(path) as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)


class PipelineTest(unittest.TestCase):
    def test_sample_invoices_end_to_end(self):
        out = tempfile.mkdtemp()
        results = process_dir("sample_invoices", os.path.join(out, "l.db"), out)
        self.assertEqual([r["decision"] for r in results],
                         ["post", "post", "post", "post", "review", "reject", "reject", "review"])
        self.assertIn("amount_anomaly", codes(results[4]["flags"]))
        self.assertIn("line_items_mismatch", codes(results[5]["flags"]))
        self.assertIn("duplicate", codes(results[6]["flags"]))
        self.assertIn("missing_po", codes(results[7]["flags"]))
        with open(os.path.join(out, "exceptions.csv")) as f:
            self.assertEqual(len(list(csv.DictReader(f))), 4)

    def test_extraction_failure_goes_to_exceptions(self):
        def down(*a, **k):
            raise llm.LLMError("provider down")
        out = tempfile.mkdtemp()
        results = process_dir("sample_invoices", os.path.join(out, "l.db"), out, complete_fn=down)
        self.assertTrue(all(r["decision"] == "review" for r in results))
        self.assertEqual(results[0]["flags"][0]["code"], "extraction_failed")


if __name__ == "__main__":
    unittest.main()
