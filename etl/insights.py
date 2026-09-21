"""Run the business-question SQL and write the answers to output/insights.md."""

import os
import re
import sqlite3

from .rules import DB_PATH, OUT_DIR, ROOT

QUERIES_PATH = os.path.join(ROOT, "sql", "analysis_queries.sql")
OUT_MD = os.path.join(OUT_DIR, "insights.md")


def _split_queries(text):
    parts = re.split(r"^-- name:\s*(.+)$", text, flags=re.MULTILINE)
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]


def _md_table(columns, rows):
    def fmt(v, col):
        if v is None:
            return "-"
        if isinstance(v, float):
            return f"{v:,.2f}" if "revenue" in col else f"{v:.1f}"
        return str(v)
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    lines += ["| " + " | ".join(fmt(v, c) for v, c in zip(row, columns)) + " |" for row in rows]
    return "\n".join(lines)


def run_insights():
    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = _split_queries(f.read())
    conn = sqlite3.connect(DB_PATH)
    out = ["# Business insights (generated from the warehouse)\n",
           "_Synthetic sample data. Each section is answered by a query in "
           "`sql/analysis_queries.sql`._\n"]
    try:
        for title, sql in queries:
            cur = conn.execute(sql)
            cols = [d[0] for d in cur.description]
            out.append(f"\n## {title}\n")
            out.append(_md_table(cols, cur.fetchall()) + "\n")
    finally:
        conn.close()
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return OUT_MD
