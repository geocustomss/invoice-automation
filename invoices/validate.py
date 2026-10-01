"""Deterministic checks on extracted invoices. The model's output is never trusted to approve itself."""
from datetime import date

from . import ledger

TOL = 0.01
ANOMALY_MULTIPLE = 3.0


def check_invoice(inv: dict, db: str) -> list[dict]:
    flags = []

    def flag(code: str, severity: str, detail: str) -> None:
        flags.append({"code": code, "severity": severity, "detail": detail})

    line_sum = round(sum(i["amount"] for i in inv["line_items"]), 2)
    if abs(line_sum - inv["subtotal"]) > TOL:
        flag("line_items_mismatch", "error", f"line items sum to {line_sum:.2f} but subtotal is {inv['subtotal']:.2f}")
    if abs(inv["subtotal"] + inv["tax"] - inv["total"]) > TOL:
        flag("total_mismatch", "error", f"subtotal + tax = {inv['subtotal'] + inv['tax']:.2f} but total is {inv['total']:.2f}")
    for i in inv["line_items"]:
        if abs(i["qty"] * i["unit_price"] - i["amount"]) > TOL:
            flag("line_math", "error", f"'{i['description']}': {i['qty']} x {i['unit_price']} != {i['amount']}")
    if date.fromisoformat(inv["due_date"]) < date.fromisoformat(inv["invoice_date"]):
        flag("due_before_invoice", "error", "due date is before invoice date")
    if ledger.is_duplicate(db, inv["vendor"], inv["invoice_number"]):
        flag("duplicate", "error", f"{inv['vendor']} {inv['invoice_number']} already processed")
    if not inv.get("po_number"):
        flag("missing_po", "warn", "no purchase order number")
    median = ledger.median_total(db, inv["vendor"])
    if median and inv["total"] > ANOMALY_MULTIPLE * median:
        flag("amount_anomaly", "warn", f"total {inv['total']:.2f} is {inv['total'] / median:.1f}x this vendor's median ({median:.2f})")
    return flags


def decide(flags: list[dict]) -> str:
    if any(f["severity"] == "error" for f in flags):
        return "reject"
    if any(f["severity"] == "warn" for f in flags):
        return "review"
    return "post"
