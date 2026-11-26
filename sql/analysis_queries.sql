-- Sales analysis queries (SQLite syntax).
-- Load data/orders.csv into a table named "orders" first, e.g. in the sqlite3 shell:
--   .mode csv
--   .import data/orders.csv orders

-- 1. Revenue, orders and average order value by Australian financial year (July to June)
SELECT
    'FY' || substr(CAST(strftime('%Y', order_date) + (CAST(strftime('%m', order_date) AS INTEGER) >= 7) AS TEXT), 3, 2) AS fy,
    ROUND(SUM(revenue), 2)                    AS revenue,
    COUNT(*)                                  AS orders,
    ROUND(SUM(revenue) / COUNT(*), 2)         AS avg_order_value,
    ROUND(100.0 * SUM(freight_cost) / SUM(revenue), 2) AS freight_pct
FROM orders
GROUP BY fy
ORDER BY fy;

-- 2. Category share of revenue and freight burden
SELECT
    category,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM orders), 1) AS share_pct,
    ROUND(100.0 * SUM(freight_cost) / SUM(revenue), 1) AS freight_pct
FROM orders
GROUP BY category
ORDER BY revenue DESC;

-- 3. Top 10 customers and their running share of total revenue
WITH by_customer AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
          / (SELECT SUM(revenue) FROM by_customer), 1) AS cumulative_share_pct
FROM by_customer
ORDER BY revenue DESC
LIMIT 10;

-- 4. Freight cost as a share of revenue by region
SELECT
    region,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(100.0 * SUM(freight_cost) / SUM(revenue), 1) AS freight_pct
FROM orders
GROUP BY region
ORDER BY freight_pct DESC;

-- 5. Monthly revenue with month-on-month change
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month, SUM(revenue) AS revenue
    FROM orders
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / LAG(revenue) OVER (ORDER BY month), 1) AS mom_change_pct
FROM monthly
ORDER BY month;
