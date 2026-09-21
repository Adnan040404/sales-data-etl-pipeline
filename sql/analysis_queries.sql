-- Business questions answered in SQL. Each block starts with "-- name: <id>"
-- and is executed by etl/insights.py, which writes the results to
-- output/insights.md.

-- name: Monthly revenue and month-over-month growth
WITH m AS (
    SELECT month, SUM(revenue) AS revenue
    FROM sales
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS mom_growth_pct
FROM m
ORDER BY month;

-- name: Product concentration (cumulative share of revenue)
WITH p AS (
    SELECT product, SUM(revenue) AS revenue
    FROM sales
    GROUP BY product
)
SELECT product,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
             / SUM(revenue) OVER (), 1) AS cumulative_share_pct
FROM p
ORDER BY revenue DESC;

-- name: Top 3 products in each sales channel
WITH x AS (
    SELECT channel, product, SUM(revenue) AS revenue
    FROM sales
    GROUP BY channel, product
),
r AS (
    SELECT *, RANK() OVER (PARTITION BY channel ORDER BY revenue DESC) AS rnk
    FROM x
)
SELECT channel, rnk AS rank, product, ROUND(revenue, 2) AS revenue
FROM r
WHERE rnk <= 3
ORDER BY channel, rnk;

-- name: Top 10 customers by revenue
SELECT customer,
       COUNT(*)                                                     AS orders,
       ROUND(SUM(revenue), 2)                                       AS revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM sales), 1) AS share_pct
FROM sales
WHERE customer <> 'Unknown'
GROUP BY customer
ORDER BY revenue DESC
LIMIT 10;

-- name: Customer loyalty segments
WITH c AS (
    SELECT customer, COUNT(*) AS orders
    FROM sales
    WHERE customer <> 'Unknown'
    GROUP BY customer
)
SELECT CASE WHEN orders = 1 THEN '1 order'
            WHEN orders <= 5 THEN '2-5 orders'
            ELSE '6+ orders' END AS segment,
       COUNT(*) AS customers
FROM c
GROUP BY segment
ORDER BY MIN(orders);
