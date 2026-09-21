-- Warehouse schema for the cleaned sales data (SQLite).
-- Constraints act as a second safety net after the transform stage: if a bad
-- row ever slips through cleaning, the database refuses it.

CREATE TABLE IF NOT EXISTS sales (
    sale_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     TEXT    NOT NULL,
    order_date   TEXT    NOT NULL,                 -- ISO yyyy-mm-dd
    month        TEXT    NOT NULL,                 -- yyyy-mm
    customer     TEXT    NOT NULL,
    product      TEXT    NOT NULL,
    channel      TEXT    NOT NULL,
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    unit_price   REAL    NOT NULL CHECK (unit_price > 0),
    discount     REAL    NOT NULL CHECK (discount >= 0 AND discount < 1),
    revenue      REAL    NOT NULL,                 -- quantity * unit_price * (1 - discount)
    source_file  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sales_month   ON sales(month);
CREATE INDEX IF NOT EXISTS ix_sales_product ON sales(product);

-- Rows the pipeline refused to load, kept with the reason for follow-up.
CREATE TABLE IF NOT EXISTS rejected_rows (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file       TEXT,
    order_id          TEXT,
    order_date_raw    TEXT,
    product_raw       TEXT,
    quantity_raw      TEXT,
    unit_price_raw    TEXT,
    reason            TEXT NOT NULL
);

-- One audit row per pipeline run (never deleted), so history is traceable.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at              TEXT    NOT NULL,
    rows_received       INTEGER NOT NULL,
    duplicates_removed  INTEGER NOT NULL,
    rows_rejected       INTEGER NOT NULL,
    rows_loaded         INTEGER NOT NULL,
    revenue_loaded      REAL    NOT NULL
);

-- Reporting views: the report and any BI tool read these, not the raw table.
DROP VIEW IF EXISTS v_monthly_kpis;
CREATE VIEW v_monthly_kpis AS
SELECT month,
       COUNT(*)                                  AS orders,
       SUM(quantity)                             AS units,
       ROUND(SUM(revenue), 2)                    AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2)         AS avg_order_value
FROM sales
GROUP BY month;

DROP VIEW IF EXISTS v_product_performance;
CREATE VIEW v_product_performance AS
SELECT product,
       SUM(quantity)                                        AS units,
       ROUND(SUM(revenue), 2)                               AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct
FROM sales
GROUP BY product;

DROP VIEW IF EXISTS v_channel_performance;
CREATE VIEW v_channel_performance AS
SELECT channel,
       COUNT(*)                                             AS orders,
       ROUND(SUM(revenue), 2)                               AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct
FROM sales
GROUP BY channel;
