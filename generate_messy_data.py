"""
Generates realistic MESSY sales exports from three different sources, so the
cleaning pipeline has something real to fix. All data is synthetic.

Each source uses different column names, date formats, price formats and
discount formats, and has deliberate defects: duplicates, missing customers,
blank/invalid prices, zero/negative quantities, inconsistent product and
channel spellings, and stray whitespace.
"""

import os
import random
from datetime import date, timedelta

import pandas as pd

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

PRODUCTS = [
    ("USB-C Cable", 12.99), ("Wireless Mouse", 24.50), ("Mechanical Keyboard", 89.00),
    ("27-inch Monitor", 219.00), ("Laptop Stand", 34.99), ("Webcam HD", 59.00),
    ("Noise-Cancelling Headphones", 149.00), ("Bluetooth Speaker", 79.00),
    ("Docking Station", 129.00), ("External SSD 1TB", 99.00),
    ("Smart LED Lamp", 29.99), ("Ergonomic Chair", 249.00),
]
FIRST = ["Ayesha", "Daniel", "Sofia", "Omar", "Hannah", "Liam", "Fatima", "Noah", "Zara",
         "Ethan", "Maya", "Hassan", "Olivia", "Ali", "Emma", "Bilal", "Chloe", "Usman"]
LAST = ["Khan", "Miller", "Rossi", "Ahmed", "Clarke", "Walker", "Malik", "Brown", "Hussain",
        "Davis", "Patel", "Sheikh", "Wilson", "Raza", "Taylor", "Iqbal", "Moore", "Butt"]
START = date(2026, 1, 1)
DAYS = 180


def customer():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


def product_variant(name):
    return random.choice([
        name, name, name, name.lower(), name.upper(),
        f" {name}", f"{name} ", name.replace("-", " "),
    ])


def base_rows(prefix, start_no, n):
    rows = []
    for i in range(n):
        pname, base = random.choice(PRODUCTS)
        rows.append({
            "id": f"{prefix}{start_no + i}",
            "date": START + timedelta(days=random.randint(0, DAYS - 1)),
            "customer": customer(),
            "product": pname,
            "qty": random.choice([1, 1, 1, 2, 2, 3, 4, 5]),
            "price": round(base * random.uniform(0.97, 1.03), 2),
            "disc": random.choice([0, 0, 0, 5, 10, 15]),
        })
    return rows


def inject_defects(rows, dup_rate=0.03):
    for r in rows:
        x = random.random()
        if x < 0.04:
            r["customer"] = random.choice(["", None, "  "])
        y = random.random()
        if y < 0.012:
            r["price"] = random.choice([None, "N/A", ""])
        z = random.random()
        if z < 0.012:
            r["qty"] = random.choice([0, -1])
    dups = random.sample(rows, int(len(rows) * dup_rate))
    return rows + [dict(d) for d in dups]


# ---- Source 1: physical store (North) -> CSV, dd/mm/yyyy, "$1,299.00", "10%"
north = inject_defects(base_rows("N-", 1001, 420))
random.shuffle(north)
pd.DataFrame([{
    "Order ID": r["id"],
    "Order Date": r["date"].strftime("%d/%m/%Y"),
    "Customer Name": r["customer"],
    "Product": product_variant(r["product"]),
    "Qty": r["qty"],
    "Unit Price": (f"${r['price']:,.2f}" if isinstance(r["price"], float) else r["price"]),
    "Discount %": f"{r['disc']}%",
    "Channel": random.choice(["In-Store", "In-Store", "in store", "IN-STORE "]),
} for r in north]).to_csv(os.path.join(RAW, "north_store.csv"), index=False)

# ---- Source 2: web shop -> CSV, mixed date formats, decimal discounts
online = inject_defects(base_rows("W", 50001, 520))
random.shuffle(online)
pd.DataFrame([{
    "order_id": r["id"],
    "date": (r["date"].strftime("%Y-%m-%d") if random.random() < 0.8
             else r["date"].strftime("%b %d, %Y")),
    "customer": r["customer"],
    "item": product_variant(r["product"]),
    "quantity": (f"{r['qty']} pcs" if isinstance(r["qty"], int) and r["qty"] > 1
                 and random.random() < 0.04 else r["qty"]),
    "price": r["price"],
    "discount": round(r["disc"] / 100, 2),
    "channel": random.choice(["Web", "web ", "WEB", "Website", "Web"]),
} for r in online]).to_csv(os.path.join(RAW, "online_shop.csv"), index=False)

# ---- Source 3: South store -> real Excel dates/numbers, different headers
south = inject_defects(base_rows("S/", 7001, 360))
random.shuffle(south)
pd.DataFrame([{
    "OrderNo": r["id"],
    "OrderDate": pd.Timestamp(r["date"]),
    "Client": r["customer"],
    "Product Name": product_variant(r["product"]),
    "Units": r["qty"],
    "Price": r["price"],
    "Disc": r["disc"],
    "Sales Channel": random.choice(["Store", "store ", "Store"]),
} for r in south]).to_excel(os.path.join(RAW, "south_store.xlsx"), index=False)

print("Raw rows written:", len(north), len(online), len(south),
      "| total", len(north) + len(online) + len(south))
