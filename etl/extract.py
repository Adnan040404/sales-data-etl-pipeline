"""EXTRACT: read every CSV/Excel file in data/raw/ and standardise headers."""

import glob
import os

import pandas as pd

from .rules import HEADER_MAP, RAW_DIR, key


# ----------------------------------------------------------------- load + clean
def load_sources():
    frames = []
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*"))):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(path, dtype=object)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path, dtype=object)
        else:
            continue
        renames = {}
        for col in df.columns:
            std = HEADER_MAP.get(key(col))
            if std:
                renames[col] = std
        log_headers = sum(1 for c, s in renames.items() if c != s)
        df = df.rename(columns=renames)
        df["source_file"] = os.path.basename(path)
        frames.append((df, log_headers))
    return frames
