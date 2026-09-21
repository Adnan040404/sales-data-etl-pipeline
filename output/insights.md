# Business insights (generated from the warehouse)

_Synthetic sample data. Each section is answered by a query in `sql/analysis_queries.sql`._


## Monthly revenue and month-over-month growth

| month | revenue | mom_growth_pct |
|---|---|---|
| 2026-01 | 50,703.34 | - |
| 2026-02 | 42,870.03 | -15.4 |
| 2026-03 | 50,074.96 | 16.8 |
| 2026-04 | 49,884.67 | -0.4 |
| 2026-05 | 52,511.66 | 5.3 |
| 2026-06 | 44,884.66 | -14.5 |


## Product concentration (cumulative share of revenue)

| product | revenue | cumulative_share_pct |
|---|---|---|
| Ergonomic Chair | 61,516.36 | 21.1 |
| 27-inch Monitor | 56,830.88 | 40.7 |
| Noise-Cancelling Headphones | 44,743.09 | 56.1 |
| Docking Station | 28,319.55 | 65.8 |
| Mechanical Keyboard | 23,418.55 | 73.8 |
| Bluetooth Speaker | 20,386.07 | 80.8 |
| External SSD 1TB | 20,341.43 | 87.8 |
| Webcam HD | 13,027.19 | 92.3 |
| Laptop Stand | 8,665.98 | 95.3 |
| Smart LED Lamp | 5,866.95 | 97.3 |
| Wireless Mouse | 4,941.57 | 99.0 |
| USB-C Cable | 2,871.70 | 100.0 |


## Top 3 products in each sales channel

| channel | rank | product | revenue |
|---|---|---|---|
| In-Store | 1 | Ergonomic Chair | 36,184.09 |
| In-Store | 2 | 27-inch Monitor | 35,119.67 |
| In-Store | 3 | Noise-Cancelling Headphones | 27,805.75 |
| Online | 1 | Ergonomic Chair | 25,332.27 |
| Online | 2 | 27-inch Monitor | 21,711.21 |
| Online | 3 | Noise-Cancelling Headphones | 16,937.34 |


## Top 10 customers by revenue

| customer | orders | revenue | share_pct |
|---|---|---|---|
| Hassan Khan | 6 | 3,723.90 | 1.3 |
| Olivia Iqbal | 5 | 3,476.27 | 1.2 |
| Sofia Taylor | 8 | 3,060.39 | 1.1 |
| Noah Raza | 8 | 2,795.21 | 1.0 |
| Ayesha Raza | 8 | 2,717.29 | 0.9 |
| Noah Rossi | 9 | 2,607.69 | 0.9 |
| Usman Brown | 7 | 2,527.61 | 0.9 |
| Chloe Ahmed | 8 | 2,522.47 | 0.9 |
| Ali Wilson | 4 | 2,426.30 | 0.8 |
| Usman Clarke | 8 | 2,379.27 | 0.8 |


## Customer loyalty segments

| segment | customers |
|---|---|
| 1 order | 28 |
| 2-5 orders | 223 |
| 6+ orders | 65 |
