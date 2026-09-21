"""TRANSFORM: parse, validate, standardise and deduplicate rows."""

import re
from datetime import date, datetime

import pandas as pd

from .rules import CHANNELS, DATE_FORMATS, PRODUCT_LOOKUP, is_blank, key


# ----------------------------------------------------------------- parsers
# Each returns (clean_value, was_changed). clean_value None = unusable.
def parse_date(v):
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.date(), False
    if isinstance(v, date):
        return v, False
    if is_blank(v):
        return None, False
    s = str(v).strip()
    for i, fmt in enumerate(DATE_FORMATS):
        try:
            return datetime.strptime(s, fmt).date(), i > 0
        except ValueError:
            continue
    return None, False


def parse_price(v):
    if is_blank(v) or str(v).strip().upper() in {"N/A", "NA", "NULL", "NONE", "-"}:
        return None, False
    if isinstance(v, (int, float)):
        return float(v), False
    s = str(v).strip()
    cleaned = s.replace("$", "").replace(",", "")
    try:
        return float(cleaned), cleaned != s
    except ValueError:
        return None, False


def parse_qty(v):
    if is_blank(v):
        return None, False
    if isinstance(v, (int, float)):
        return int(v), False
    m = re.search(r"-?\d+", str(v))
    if not m:
        return None, False
    return int(m.group()), not re.fullmatch(r"-?\d+", str(v).strip())


def parse_discount(v):
    if is_blank(v):
        return 0.0, False
    if isinstance(v, str):
        s = v.strip()
        try:
            if s.endswith("%"):
                return float(s[:-1]) / 100, True
            n = float(s)
        except ValueError:
            return 0.0, False
    else:
        n = float(v)
    return (n / 100, True) if n > 1 else (n, False)



def transform(frames):
    """TRANSFORM: clean, validate, deduplicate. Returns (clean, rejected, quality_log, received, dups)."""
    log = {k: 0 for k in [
        "headers", "trim", "product", "channel", "date", "price", "discount", "qty",
        "customer", "dups"]}
    log["headers"] = sum(h for _, h in frames)
    received = sum(len(df) for df, _ in frames)

    clean_rows, rejected = [], []
    for df, _ in frames:
        for _, r in df.iterrows():
            raw = {c: r.get(c) for c in
                   ["order_id", "order_date", "customer", "product", "quantity", "unit_price",
                    "discount", "channel"]}
            src = r["source_file"]

            dt, dt_ch = parse_date(raw["order_date"])
            price, price_ch = parse_price(raw["unit_price"])
            qty, qty_ch = parse_qty(raw["quantity"])
            disc, disc_ch = parse_discount(raw["discount"])

            reason = None
            if dt is None:
                reason = "Unreadable or missing date"
            elif price is None or price <= 0:
                reason = "Missing or invalid unit price"
            elif qty is None or qty <= 0:
                reason = "Zero or negative quantity"
            if reason:
                rejected.append({
                    "Source": src, "Order ID": str(raw["order_id"]).strip(),
                    "Order Date (raw)": raw["order_date"], "Product (raw)": raw["product"],
                    "Quantity (raw)": raw["quantity"], "Unit Price (raw)": raw["unit_price"],
                    "Reason": reason})
                continue

            log["date"] += dt_ch
            log["price"] += price_ch
            log["qty"] += qty_ch
            log["discount"] += disc_ch

            def trimmed(v):
                s = "" if is_blank(v) else str(v)
                return s.strip(), (s != s.strip())

            cust, c_tr = trimmed(raw["customer"])
            prod_raw, p_tr = trimmed(raw["product"])
            chan_raw, ch_tr = trimmed(raw["channel"])
            log["trim"] += c_tr + p_tr + ch_tr
            if not cust:
                cust = "Unknown"
                log["customer"] += 1

            prod = PRODUCT_LOOKUP.get(key(prod_raw), prod_raw.title())
            log["product"] += prod != prod_raw
            chan = CHANNELS.get(key(chan_raw), chan_raw.title())
            log["channel"] += chan != chan_raw

            clean_rows.append({
                "Order ID": str(raw["order_id"]).strip(), "Order Date": dt, "Customer": cust,
                "Product": prod, "Channel": chan, "Quantity": qty, "Unit Price": round(price, 2),
                "Discount": round(disc, 4), "Source File": src})

    clean = pd.DataFrame(clean_rows)
    before = len(clean)
    clean = clean.drop_duplicates(
        subset=["Order ID", "Order Date", "Product", "Quantity", "Unit Price", "Discount"])
    log["dups"] = before - len(clean)
    clean = clean.sort_values(["Order Date", "Order ID"]).reset_index(drop=True)
    rej = pd.DataFrame(rejected)

    quality = [
        ("Column headers standardised across sources", log["headers"],
         "Different names for the same field mapped to one schema"),
        ("Text trimmed (stray leading/trailing spaces)", log["trim"],
         "Spaces removed from names, products and channels"),
        ("Product names standardised", log["product"],
         "Case, hyphen and spacing variants mapped to one product name"),
        ("Channel labels unified", log["channel"],
         "Web/web/WEB/Website -> Online; Store variants -> In-Store"),
        ("Dates converted to one format", log["date"],
         "Text dates in several formats parsed into real dates"),
        ("Prices cleaned", log["price"], "Currency symbols and thousands separators removed"),
        ("Discounts normalised to a decimal", log["discount"],
         "'10%', 10 and 0.10 all become 0.10"),
        ("Quantities cleaned", log["qty"], "Text such as '2 pcs' converted to the number 2"),
        ("Missing customer names filled", log["customer"], "Set to 'Unknown' (kept, not dropped)"),
        ("Duplicate rows removed", log["dups"],
         "Same order, date, product, quantity, price and discount"),
    ]
    return clean, rej, quality, received, log["dups"]


