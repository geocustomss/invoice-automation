"""CSV exports: a QuickBooks-style bill import for approved invoices and an exceptions queue."""
import csv

ACCOUNT_RULES = [("reagent", "Lab Supplies"), ("consumable", "Lab Supplies"), ("shipping", "Freight & Shipping"),
                 ("carton", "Freight & Shipping"), ("hosting", "Software & Hosting")]
DEFAULT_ACCOUNT = "Uncategorized Expense"


def categorize(description: str) -> str:
    low = description.lower()
    return next((acct for kw, acct in ACCOUNT_RULES if kw in low), DEFAULT_ACCOUNT)


def write_bills(path: str, invoices: list[dict]) -> int:
    """One row per line item. Column names are QuickBooks-style; adjust to your import template."""
    rows = 0
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["BillNo", "Vendor", "BillDate", "DueDate", "PONumber", "Account", "LineDescription",
                    "LineAmount", "Currency"])
        for inv in invoices:
            for item in inv["line_items"]:
                w.writerow([inv["invoice_number"], inv["vendor"], inv["invoice_date"], inv["due_date"],
                            inv.get("po_number") or "", categorize(item["description"]), item["description"],
                            f"{item['amount']:.2f}", inv["currency"]])
                rows += 1
    return rows


def write_exceptions(path: str, items: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Source", "Vendor", "InvoiceNo", "Decision", "Reasons"])
        for e in items:
            w.writerow([e["source"], e.get("vendor", ""), e.get("invoice_number", ""), e["decision"],
                        "; ".join(f"{x['code']}: {x['detail']}" for x in e["flags"])])
