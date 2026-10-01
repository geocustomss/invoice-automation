"""SQLite ledger of processed invoices, used for duplicate and anomaly checks."""
import sqlite3
import statistics
import time


def _conn(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vendor TEXT, invoice_number TEXT, total REAL,
        status TEXT, created REAL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vendor ON invoices(vendor, invoice_number)")
    return conn


def _key(vendor: str, number: str) -> tuple[str, str]:
    return vendor.strip().lower(), number.strip().upper()


def add(db: str, vendor: str, number: str, total: float, status: str) -> None:
    v, n = _key(vendor, number)
    with _conn(db) as c:
        c.execute("INSERT INTO invoices (vendor, invoice_number, total, status, created) VALUES (?,?,?,?,?)",
                  (v, n, total, status, time.time()))


def is_duplicate(db: str, vendor: str, number: str) -> bool:
    """Rejected invoices can be resubmitted corrected; posted or in-review ones can't be re-entered."""
    v, n = _key(vendor, number)
    with _conn(db) as c:
        row = c.execute("SELECT 1 FROM invoices WHERE vendor=? AND invoice_number=? AND status IN ('post','review')",
                        (v, n)).fetchone()
    return row is not None


def median_total(db: str, vendor: str, min_history: int = 3):
    v = vendor.strip().lower()
    with _conn(db) as c:
        totals = [r[0] for r in c.execute("SELECT total FROM invoices WHERE vendor=? AND status='post'", (v,))]
    return statistics.median(totals) if len(totals) >= min_history else None
