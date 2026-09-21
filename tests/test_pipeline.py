"""Unit tests for the parsers plus end-to-end integrity checks for the pipeline."""

import os
import sqlite3
import sys
from datetime import date

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.extract import load_sources  # noqa: E402
from etl.load import load  # noqa: E402
from etl.rules import DB_PATH  # noqa: E402
from etl.transform import (parse_date, parse_discount, parse_price,  # noqa: E402
                           parse_qty, transform)


# ---------------------------------------------------------------- parsers
def test_dates_in_all_supported_formats():
    assert parse_date("2026-03-05") == (date(2026, 3, 5), False)
    assert parse_date("05/03/2026") == (date(2026, 3, 5), True)      # day-first
    assert parse_date("Mar 5, 2026") == (date(2026, 3, 5), True)
    assert parse_date(pd.Timestamp("2026-03-05")) == (date(2026, 3, 5), False)


def test_unreadable_dates_are_rejected_not_guessed():
    assert parse_date("not a date")[0] is None
    assert parse_date("")[0] is None
    assert parse_date(None)[0] is None


def test_price_cleaning():
    assert parse_price("$1,299.00") == (1299.0, True)
    assert parse_price(12.5) == (12.5, False)
    assert parse_price("N/A")[0] is None
    assert parse_price("")[0] is None


def test_quantity_cleaning():
    assert parse_qty("3") == (3, False)
    assert parse_qty("2 pcs") == (2, True)
    assert parse_qty(4) == (4, False)
    assert parse_qty("abc")[0] is None


def test_discount_normalisation():
    assert parse_discount("10%") == (0.1, True)
    assert parse_discount(10) == (0.1, True)
    assert parse_discount(0.15) == (0.15, False)
    assert parse_discount("0.05") == (0.05, False)
    assert parse_discount(None) == (0.0, False)


# ---------------------------------------------------------------- pipeline integrity
def _run():
    frames = load_sources()
    return frames, transform(frames)


def test_every_input_row_is_accounted_for():
    frames, (clean, rej, _, received, dups) = _run()
    assert received == sum(len(df) for df, _ in frames)
    assert received == len(clean) + dups + len(rej)


def test_clean_data_has_no_invalid_values():
    _, (clean, *_rest) = _run()
    assert (clean["Quantity"] > 0).all()
    assert (clean["Unit Price"] > 0).all()
    assert clean["Discount"].between(0, 1, inclusive="left").all()
    assert clean["Customer"].str.strip().ne("").all()
    assert set(clean["Channel"]) <= {"Online", "In-Store"}


def test_no_duplicates_remain():
    _, (clean, *_rest) = _run()
    keys = ["Order ID", "Order Date", "Product", "Quantity", "Unit Price", "Discount"]
    assert not clean.duplicated(subset=keys).any()


def test_load_is_idempotent_and_matches_transform():
    _, (clean, rej, _, received, dups) = _run()
    first = load(clean, rej, received, dups)
    second = load(clean, rej, received, dups)      # re-run must not double-count
    assert first["rows_loaded"] == second["rows_loaded"] == len(clean)
    conn = sqlite3.connect(DB_PATH)
    try:
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == len(clean)
        # Independent check: exact Decimal arithmetic, half-up rounding per line.
        from decimal import ROUND_HALF_UP, Decimal
        expected = sum(
            (Decimal(int(r.Quantity)) * Decimal(str(r._7)) * (1 - Decimal(str(r.Discount)))
             ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            for r in clean.rename(columns={"Unit Price": "_7"}).itertuples())
        expected = float(expected)
        actual = conn.execute("SELECT ROUND(SUM(revenue), 2) FROM sales").fetchone()[0]
        assert abs(actual - expected) < 0.01
    finally:
        conn.close()
