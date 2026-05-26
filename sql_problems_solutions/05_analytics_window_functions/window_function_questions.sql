-- Window Function SQL Problems and Solutions

-- 1. Rank products by revenue within category.
SELECT category_id, product_id, SUM(amount) AS revenue,
       RANK() OVER (PARTITION BY category_id ORDER BY SUM(amount) DESC) AS revenue_rank
FROM order_items
GROUP BY category_id, product_id;

-- 2. Calculate day-over-day sales change.
WITH daily AS (
    SELECT CAST(order_date AS DATE) AS order_day, SUM(amount) AS sales
    FROM orders
    GROUP BY CAST(order_date AS DATE)
)
SELECT order_day, sales, sales - LAG(sales) OVER (ORDER BY order_day) AS sales_change
FROM daily;

-- 3. Seven-day moving average.
WITH daily AS (
    SELECT CAST(order_date AS DATE) AS order_day, SUM(amount) AS sales
    FROM orders
    GROUP BY CAST(order_date AS DATE)
)
SELECT order_day, sales,
       AVG(sales) OVER (ORDER BY order_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS seven_day_avg
FROM daily;

-- 4. First and last order amount per customer.
SELECT DISTINCT customer_id,
       FIRST_VALUE(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS first_order_amount,
       FIRST_VALUE(amount) OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS last_order_amount
FROM orders;

-- 5. Top 3 orders per customer.
WITH ranked AS (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rn
    FROM orders o
)
SELECT *
FROM ranked
WHERE rn <= 3;
