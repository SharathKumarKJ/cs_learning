-- Advanced window function patterns

-- 1. Percent of total per category.
SELECT category_id, product_id, revenue,
       revenue * 100.0 / SUM(revenue) OVER (PARTITION BY category_id) AS pct_of_category
FROM product_revenue;

-- 2. NTILE for quartiles.
SELECT customer_id, total_spent, NTILE(4) OVER (ORDER BY total_spent DESC) AS quartile
FROM customer_totals;

-- 3. LEAD/LAG for time-based comparisons.
SELECT customer_id, order_date, amount,
       LAG(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_amount,
       LEAD(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS next_amount
FROM orders;

-- 4. Running count of distinct values approximation using window.
SELECT order_date, COUNT(*) OVER (ORDER BY order_date ROWS UNBOUNDED PRECEDING) AS running_orders
FROM orders;
