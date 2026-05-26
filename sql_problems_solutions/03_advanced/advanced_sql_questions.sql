-- Advanced SQL Problems and Solutions

-- 1. Latest order per customer.
WITH ranked_orders AS (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC) AS rn
    FROM orders o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;

-- 2. Customers with increasing order amounts.
WITH previous_orders AS (
    SELECT o.*, LAG(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_amount
    FROM orders o
)
SELECT *
FROM previous_orders
WHERE previous_amount IS NOT NULL AND amount > previous_amount;

-- 3. Running monthly revenue.
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS sales_month, SUM(amount) AS monthly_revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT sales_month, monthly_revenue,
       SUM(monthly_revenue) OVER (ORDER BY sales_month) AS running_revenue
FROM monthly;

-- 4. Second highest salary by department.
WITH ranked AS (
    SELECT employee_id, department_id, salary,
           DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank
    FROM employees
)
SELECT *
FROM ranked
WHERE salary_rank = 2;

-- 5. Find gaps in daily order dates.
WITH dates AS (
    SELECT DISTINCT CAST(order_date AS DATE) AS order_day
    FROM orders
), gaps AS (
    SELECT order_day, LAG(order_day) OVER (ORDER BY order_day) AS previous_day
    FROM dates
)
SELECT previous_day, order_day, order_day - previous_day AS gap_days
FROM gaps
WHERE previous_day IS NOT NULL AND order_day - previous_day > 1;

-- 6. Customer retention by month.
WITH customer_month AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS order_month
    FROM orders
), first_month AS (
    SELECT customer_id, MIN(order_month) AS cohort_month
    FROM customer_month
    GROUP BY customer_id
)
SELECT f.cohort_month, c.order_month, COUNT(DISTINCT c.customer_id) AS retained_customers
FROM customer_month c
JOIN first_month f ON c.customer_id = f.customer_id
GROUP BY f.cohort_month, c.order_month
ORDER BY f.cohort_month, c.order_month;
