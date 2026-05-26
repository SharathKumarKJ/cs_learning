-- Pivot and unpivot

-- 1. Pivot monthly sales (PostgreSQL crosstab style with conditional aggregation).
SELECT customer_id,
       SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 1 THEN amount END) AS jan,
       SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 2 THEN amount END) AS feb,
       SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 3 THEN amount END) AS mar
FROM orders
GROUP BY customer_id;

-- 2. Unpivot wide table using UNION ALL.
SELECT customer_id, 'jan' AS month, jan AS amount FROM monthly_sales WHERE jan IS NOT NULL
UNION ALL
SELECT customer_id, 'feb', feb FROM monthly_sales WHERE feb IS NOT NULL
UNION ALL
SELECT customer_id, 'mar', mar FROM monthly_sales WHERE mar IS NOT NULL;
