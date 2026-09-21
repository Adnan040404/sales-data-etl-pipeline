"""LOAD: write the cleaned data into a SQLite warehouse and verify it.

The load is idempotent: `sales` and `rejected_rows` are fully refreshed on
every run (so re-running never double-counts), while `pipeline_runs` is an
append-only audit log.
"""

import os
import sqlite3
from datetime import datetime

from .rules import DB_PATH, ROOT, line_revenue

SCHEMA_PATH = os.path.join(ROOT, "sql", "schema.sql")


def _text(v):
    return None if v is None or str(v).strip() == "" else str(v)


def load(clean, rej, received, dups):
    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.execute("DELETE FROM sales")
        conn.execute("DELETE FROM rejected_rows")

        sales_rows = []
        for r in clean.itertuples(index=False):
            order_id, dt, cust, prod, chan, qty, price, disc, src = r
            revenue = line_revenue(qty, price, disc)
            sales_rows.append((order_id, dt.isoformat(), dt.strftime("%Y-%m"), cust, prod,
                               chan, int(qty), float(price), float(disc), revenue, src))
        conn.executemany(
            "INSERT INTO sales (order_id, order_date, month, customer, product, channel, "
            "quantity, unit_price, discount, revenue, source_file) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)", sales_rows)

        conn.executemany(
            "INSERT INTO rejected_rows (source_file, order_id, order_date_raw, product_raw, "
            "quantity_raw, unit_price_raw, reason) VALUES (?,?,?,?,?,?,?)",
            [(_text(r[0]), _text(r[1]), _text(r[2]), _text(r[3]), _text(r[4]), _text(r[5]),
              r[6]) for r in rej.itertuples(index=False)])

        loaded, revenue = conn.execute(
            "SELECT COUNT(*), ROUND(SUM(revenue), 2) FROM sales").fetchone()

        # Verification: what is in the database must equal what the transform produced.
        expected_revenue = round(sum(row[9] for row in sales_rows), 2)
        if loaded != len(clean) or abs(revenue - expected_revenue) > 0.005:
            raise RuntimeError(
                f"Load verification failed: db has {loaded} rows / {revenue}, "
                f"expected {len(clean)} rows / {expected_revenue}")
        if received != loaded + dups + len(rej):
            raise RuntimeError("Row accounting failed: received != loaded + duplicates + rejected")

        conn.execute(
            "INSERT INTO pipeline_runs (run_at, rows_received, duplicates_removed, "
            "rows_rejected, rows_loaded, revenue_loaded) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), received, dups, len(rej),
             loaded, revenue))
        conn.commit()
        return {"rows_loaded": loaded, "revenue": revenue, "db": DB_PATH}
    finally:
        conn.close()
