"""Cleaning rules and small helpers shared by the ETL stages.

Everything a new data source might need to change lives here (column-name
synonyms, product list, channel labels, accepted date formats) so the
transform logic itself never has to be edited to onboard a new source.
"""

import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
OUT_DIR = os.path.join(ROOT, "output")
OUT_XLSX = os.path.join(OUT_DIR, "Sales_Report.xlsx")
DB_PATH = os.path.join(OUT_DIR, "sales_warehouse.db")
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------------------------------------------- config
# Different sources name the same column differently. Keys are header text
# with everything except letters/digits removed and lower-cased.
HEADER_MAP = {
    "orderid": "order_id", "orderno": "order_id",
    "orderdate": "order_date", "date": "order_date",
    "customername": "customer", "customer": "customer", "client": "customer",
    "product": "product", "item": "product", "productname": "product",
    "qty": "quantity", "quantity": "quantity", "units": "quantity",
    "unitprice": "unit_price", "price": "unit_price",
    "discount": "discount", "disc": "discount",
    "channel": "channel", "saleschannel": "channel",
}
PRODUCTS = [
    "USB-C Cable", "Wireless Mouse", "Mechanical Keyboard", "27-inch Monitor",
    "Laptop Stand", "Webcam HD", "Noise-Cancelling Headphones", "Bluetooth Speaker",
    "Docking Station", "External SSD 1TB", "Smart LED Lamp", "Ergonomic Chair",
]
CHANNELS = {"instore": "In-Store", "store": "In-Store", "web": "Online", "website": "Online"}
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"]  # slash dates are day-first


def key(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


PRODUCT_LOOKUP = {key(p): p for p in PRODUCTS}


def line_revenue(qty, price, disc):
    """Quantity x price x (1 - discount) in exact decimal arithmetic, rounded half-up to cents.

    Floats cannot represent most cent values exactly, so summing float results
    can drift by a cent. Money is computed with Decimal instead.
    """
    from decimal import ROUND_HALF_UP, Decimal
    amount = Decimal(int(qty)) * Decimal(str(price)) * (Decimal(1) - Decimal(str(disc)))
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


