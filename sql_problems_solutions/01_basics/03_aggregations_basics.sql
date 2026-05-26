-- Aggregations

-- 1. Total, average, min, max, count per group.
SELECT customer_id, COUNT(*) AS orders, SUM(amount) AS total, AVG(amount) AS avg_amt, MIN(amount) AS min_amt, MAX(amount) AS max_amt
FROM orders
GROUP BY customer_id;

-- 2. HAVING clause.
SELECT customer_id, SUM(amount) AS total
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > 1000;

-- 3. COUNT distinct.
SELECT COUNT(DISTINCT customer_id) AS unique_customers
FROM orders;

-- 4. Group by multiple columns.
SELECT customer_id, DATE_TRUNC('month', order_date) AS month, SUM(amount) AS total
FROM orders
GROUP BY customer_id, DATE_TRUNC('month', order_date);
