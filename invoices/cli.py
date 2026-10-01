import argparse
import os

from . import llm, mock
from .pipeline import process_dir


def main() -> None:
    llm.register_mock(mock.handler)
    p = argparse.ArgumentParser(prog="invoices")
    p.add_argument("directory", help="folder of invoice .txt files")
    p.add_argument("--db", default="out/ledger.db")
    p.add_argument("--out", default="out")
    p.add_argument("--provider", default="mock")
    p.add_argument("--model", default="mock-large")
    p.add_argument("--fresh", action="store_true", help="delete the ledger first")
    args = p.parse_args()
    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    if args.fresh and os.path.exists(args.db):
        os.remove(args.db)

    results = process_dir(args.directory, args.db, args.out, args.provider, args.model)
    print(f"{'file':<32}{'decision':<9}{'total':>10}  reasons")
    for r in results:
        reasons = "; ".join(f["code"] for f in r["flags"]) or "-"
        print(f"{r['source']:<32}{r['decision']:<9}{r.get('total', 0):>10.2f}  {reasons}")
    counts = {d: sum(1 for r in results if r["decision"] == d) for d in ("post", "review", "reject")}
    print(f"\n{counts}   outputs: {args.out}/bills_import.csv, {args.out}/exceptions.csv")


if __name__ == "__main__":
    main()
