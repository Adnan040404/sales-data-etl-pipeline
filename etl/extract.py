"""EXTRACT: read every CSV/Excel file in a folder and standardise the column names.

A source whose columns can't be recognised stops the run with a message that lists the
columns it did find. Without that check, every row would silently become a "rejected"
row and nobody would learn the real cause was a renamed header.
"""

import glob
import logging
import os

import pandas as pd

from .rules import HEADER_MAP, RAW_DIR, key

log = logging.getLogger("etl")

# Columns the pipeline cannot work without. Customer, discount and channel are optional
# (missing customers become "Unknown", a missing discount is 0).
REQUIRED = ["order_id", "order_date", "product", "quantity", "unit_price"]
KNOWN = set(HEADER_MAP.values()) | {"source_file"}
SUPPORTED = (".csv", ".xlsx", ".xls")


class SchemaError(ValueError):
    """A source file is missing columns the pipeline needs."""


class NoInputError(ValueError):
    """There is nothing to read."""


def _read(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        # utf-8-sig: Excel's "CSV UTF-8" adds an invisible byte-order mark to the first header
        return pd.read_csv(path, dtype=object, encoding="utf-8-sig")
    return pd.read_excel(path, dtype=object)


def load_sources(raw_dir=RAW_DIR):
    files = [p for p in sorted(glob.glob(os.path.join(raw_dir, "*")))
             if os.path.splitext(p)[1].lower() in SUPPORTED]
    if not files:
        raise NoInputError(f"No .csv or .xlsx files found in {raw_dir}")

    frames = []
    for path in files:
        name = os.path.basename(path)
        df = _read(path)
        df.columns = [str(c).strip() for c in df.columns]
        original_headers = list(df.columns)                 # as they appear in the file
        renames = {c: HEADER_MAP[key(c)] for c in df.columns if key(c) in HEADER_MAP}
        df = df.rename(columns=renames)

        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise SchemaError(
                f"{name}: no column recognised for {', '.join(missing)}. "
                f"Columns in the file: {', '.join(original_headers)}. "
                f"If a column was renamed, add its name to HEADER_MAP in etl/rules.py.")
        unknown = [c for c in df.columns if c not in KNOWN]
        if unknown:
            log.warning("%s: ignoring unrecognised column(s): %s", name, ", ".join(unknown))

        log_headers = sum(1 for c, s in renames.items() if c != s)
        df["source_file"] = name
        frames.append((df, log_headers))
    return frames
