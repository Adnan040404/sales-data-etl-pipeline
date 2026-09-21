"""
Run the full ETL pipeline end to end:

    1. EXTRACT    read every raw file in a folder
    2. TRANSFORM  clean, validate, deduplicate, quarantine bad rows
    3. LOAD       write to a SQLite warehouse and verify it
    4. REPORT     build the Excel report (live formulas)
    5. INSIGHTS   answer business questions in SQL -> output/insights.md

Usage:
    python generate_messy_data.py            # (optional) regenerate the sample raw files
    python run_pipeline.py                   # uses data/raw
    python run_pipeline.py --raw-dir path\\to\\your\\exports
"""

import argparse
import logging
import sys
import time

from etl.extract import NoInputError, SchemaError, load_sources
from etl.insights import run_insights
from etl.load import load
from etl.report import build_workbook
from etl.rules import RAW_DIR
from etl.transform import transform


def step(n, name):
    print(f"[{n}/5] {name}", flush=True)
    return time.perf_counter()


def main(argv=None):
    p = argparse.ArgumentParser(description="Sales data ETL pipeline")
    p.add_argument("--raw-dir", default=RAW_DIR, help="folder with the CSV/Excel exports (default: data/raw)")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="      ! %(message)s")

    t = step(1, "EXTRACT")
    try:
        frames = load_sources(args.raw_dir)
    except (SchemaError, NoInputError) as exc:
        print(f"Cannot continue: {exc}", file=sys.stderr)
        return 2
    received = sum(len(df) for df, _ in frames)
    print(f"      {len(frames)} source files, {received:,} rows ({time.perf_counter() - t:.2f}s)")

    t = step(2, "TRANSFORM")
    clean, rej, quality, received, dups = transform(frames)
    print(f"      clean {len(clean):,} | duplicates removed {dups} | rejected {len(rej)} "
          f"({time.perf_counter() - t:.2f}s)")
    for check, count, _ in quality:
        print(f"        - {check}: {count:,}")
    if clean.empty:
        print("Cannot continue: no valid rows survived cleaning. See the rejected rows above.",
              file=sys.stderr)
        return 2

    t = step(3, "LOAD")
    res = load(clean, rej, received, dups)
    print(f"      {res['rows_loaded']:,} rows, revenue ${res['revenue']:,.2f} verified "
          f"in {res['db']} ({time.perf_counter() - t:.2f}s)")

    t = step(4, "REPORT")
    build_workbook(clean, rej, quality, received, dups, len(frames))
    print(f"      Excel report written ({time.perf_counter() - t:.2f}s)")

    t = step(5, "INSIGHTS")
    path = run_insights()
    print(f"      {path} ({time.perf_counter() - t:.2f}s)")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
