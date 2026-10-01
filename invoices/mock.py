"""Regex parser standing in for a model, so the pipeline runs offline and in CI."""
import json
import re


def _field(text: str, label: str) -> str:
    m = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def handler(system: str, prompt: str, model: str) -> str:
    text = prompt.split("Invoice:\n", 1)[-1]
    items = [{"description": d.strip(), "qty": float(q), "unit_price": float(u), "amount": float(a)}
             for d, q, u, a in re.findall(r"^- (.+?) \| qty ([\d.]+) \| unit ([\d.]+) \| amount ([\d.]+)$", text, re.M)]
    return json.dumps({
        "vendor": _field(text, "Vendor"), "invoice_number": _field(text, "Invoice #"),
        "invoice_date": _field(text, "Invoice Date"), "due_date": _field(text, "Due Date"),
        "po_number": _field(text, "PO") or None, "currency": _field(text, "Currency") or "USD",
        "line_items": items, "subtotal": float(_field(text, "Subtotal") or 0),
        "tax": float(_field(text, "Tax") or 0), "total": float(_field(text, "Total") or 0),
    })
