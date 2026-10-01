#!/usr/bin/env bash
# Run with: bash demo.sh
# Recording helper: prints each command, then runs it. Use PAUSE=0 for an instant run.
set -e
PAUSE=${PAUSE:-1.5}
run() { echo; echo "\$ $*"; sleep "$PAUSE"; "$@"; sleep "$PAUSE"; }
run python -m invoices sample_invoices --fresh --out out
run cat out/exceptions.csv
run head -4 out/bills_import.csv
