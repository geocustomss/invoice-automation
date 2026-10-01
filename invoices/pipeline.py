from __future__ import annotations

from pathlib import Path

from . import export, ledger, llm
from .extract import extract_invoice
from .validate import check_invoice, decide


def process_dir(directory: str, db: str, out_dir: str, provider: str = "mock",
                model: str = "mock-large", complete_fn=None) -> list[dict]:
    results, posted, exceptions = [], [], []
    for path in sorted(Path(directory).glob("*.txt")):
        entry = {"source": path.name, "decision": "review", "flags": [], "cost_usd": 0.0}
        try:
            inv, cost = extract_invoice(path.read_text(), provider, model, complete_fn)
        except llm.LLMError as e:  # extraction failed: a human looks at the original document
            entry["flags"] = [{"code": "extraction_failed", "severity": "warn", "detail": str(e)[:200]}]
            exceptions.append(entry)
            results.append(entry)
            continue
        flags = check_invoice(inv, db)
        decision = decide(flags)
        ledger.add(db, inv["vendor"], inv["invoice_number"], inv["total"], decision)
        entry.update(decision=decision, flags=flags, cost_usd=cost, vendor=inv["vendor"],
                     invoice_number=inv["invoice_number"], total=inv["total"])
        (posted if decision == "post" else exceptions).append(inv if decision == "post" else entry)
        results.append(entry)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    export.write_bills(str(Path(out_dir) / "bills_import.csv"), posted)
    export.write_exceptions(str(Path(out_dir) / "exceptions.csv"), exceptions)
    return results
