-- ============================================================
-- 50 MORE SQL PROBLEMS WITH SOLUTIONS
-- Mix of basic, intermediate, advanced, and very advanced.
-- Dialect: Mostly ANSI / PostgreSQL. Some Snowflake/BigQuery notes inline.
-- Schema assumed:
--   customers(customer_id, customer_name, email, city, country, status, signup_date)
--   orders(order_id, customer_id, order_date, amount, status)
--   order_items(order_item_id, order_id, product_id, quantity, unit_price)
--   products(product_id, product_name, category_id, price)
--   categories(category_id, category_name)
--   employees(employee_id, employee_name, manager_id, department_id, salary, hire_date)
--   departments(department_id, department_name)
--   logins(user_id, login_time)
--   payments(payment_id, order_id, paid_at, amount, method)
-- ============================================================


-- ------------------------------------------------------------
-- PROBLEM 1: Find duplicate customer emails (case-insensitive).
-- Approach: lower the email and group by it; HAVING COUNT(*) > 1.
-- ------------------------------------------------------------
SELECT LOWER(email) AS email_lower, COUNT(*) AS duplicate_count
FROM customers
WHERE email IS NOT NULL
GROUP BY LOWER(email)
HAVING COUNT(*) > 1;


-- ------------------------------------------------------------
-- PROBLEM 2: Delete duplicate rows keeping the one with smallest id.
-- Approach: use ROW_NUMBER() over partition by duplicate keys.
-- ------------------------------------------------------------
WITH ranked AS (
    SELECT customer_id,
           ROW_NUMBER() OVER (PARTITION BY LOWER(email) ORDER BY customer_id) AS rn
    FROM customers
)
DELETE FROM customers
WHERE customer_id IN (SELECT customer_id FROM ranked WHERE rn > 1);


-- ------------------------------------------------------------
-- PROBLEM 3: Second highest salary overall.
-- Approach: DENSE_RANK = 2 handles ties correctly.
-- ------------------------------------------------------------
SELECT DISTINCT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rk
    FROM employees
) t
WHERE rk = 2;


-- ------------------------------------------------------------
-- PROBLEM 4: Nth highest salary per department.
-- Approach: dense_rank within department partition.
-- ------------------------------------------------------------
WITH ranked AS (
    SELECT department_id, employee_id, salary,
           DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rk
    FROM employees
)
SELECT * FROM ranked WHERE rk = 3;  -- change 3 to N


-- ------------------------------------------------------------
-- PROBLEM 5: Employees earning more than their manager.
-- Approach: self join on manager_id.
-- ------------------------------------------------------------
SELECT e.employee_id, e.employee_name, e.salary, m.employee_name AS manager_name, m.salary AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.employee_id
WHERE e.salary > m.salary;


-- ------------------------------------------------------------
-- PROBLEM 6: Department with highest average salary.
-- Approach: aggregate then order limit 1.
-- ------------------------------------------------------------
SELECT department_id, AVG(salary) AS avg_salary
FROM employees
GROUP BY department_id
ORDER BY avg_salary DESC
FETCH FIRST 1 ROWS ONLY;


-- ------------------------------------------------------------
-- PROBLEM 7: Departments with no employees.
-- Approach: LEFT JOIN + IS NULL or NOT EXISTS.
-- ------------------------------------------------------------
SELECT d.*
FROM departments d
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.department_id = d.department_id);


-- ------------------------------------------------------------
-- PROBLEM 8: Customers who placed orders in every month of 2026.
-- Approach: count distinct months per customer = 12.
-- ------------------------------------------------------------
SELECT customer_id
FROM orders
WHERE EXTRACT(YEAR FROM order_date) = 2026
GROUP BY customer_id
HAVING COUNT(DISTINCT EXTRACT(MONTH FROM order_date)) = 12;


-- ------------------------------------------------------------
-- PROBLEM 9: Customers active in Jan but not Feb (churn).
-- Approach: EXCEPT / NOT IN with subquery.
-- ------------------------------------------------------------
SELECT DISTINCT customer_id
FROM orders
WHERE order_date BETWEEN DATE '2026-01-01' AND DATE '2026-01-31'
EXCEPT
SELECT DISTINCT customer_id
FROM orders
WHERE order_date BETWEEN DATE '2026-02-01' AND DATE '2026-02-28';


-- ------------------------------------------------------------
-- PROBLEM 10: New customers per month.
-- Approach: aggregate by signup_date month.
-- ------------------------------------------------------------
SELECT DATE_TRUNC('month', signup_date) AS signup_month, COUNT(*) AS new_customers
FROM customers
GROUP BY DATE_TRUNC('month', signup_date)
ORDER BY signup_month;


-- ------------------------------------------------------------
-- PROBLEM 11: Returning customers (>= 2 orders).
-- ------------------------------------------------------------
SELECT customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 2;


-- ------------------------------------------------------------
-- PROBLEM 12: First and last order date per customer.
-- ------------------------------------------------------------
SELECT customer_id, MIN(order_date) AS first_order, MAX(order_date) AS last_order
FROM orders
GROUP BY customer_id;


-- ------------------------------------------------------------
-- PROBLEM 13: Days between consecutive orders per customer.
-- Approach: LAG to get previous order date.
-- ------------------------------------------------------------
SELECT customer_id, order_date,
       order_date - LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS days_since_prev
FROM orders;


-- ------------------------------------------------------------
-- PROBLEM 14: Customers inactive for > 90 days (churned).
-- ------------------------------------------------------------
SELECT customer_id, MAX(order_date) AS last_order
FROM orders
GROUP BY customer_id
HAVING MAX(order_date) < CURRENT_DATE - INTERVAL '90 days';


-- ------------------------------------------------------------
-- PROBLEM 15: Running total of revenue per customer ordered by date.
-- ------------------------------------------------------------
SELECT customer_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM orders;


-- ------------------------------------------------------------
-- PROBLEM 16: 30-day rolling revenue (calendar window).
-- ------------------------------------------------------------
SELECT order_date,
       SUM(SUM(amount)) OVER (ORDER BY order_date
                              RANGE BETWEEN INTERVAL '29 days' PRECEDING AND CURRENT ROW) AS rolling_30d
FROM orders
GROUP BY order_date
ORDER BY order_date;


-- ------------------------------------------------------------
-- PROBLEM 17: Top 3 products by revenue per category.
-- ------------------------------------------------------------
WITH revenue AS (
    SELECT p.category_id, oi.product_id, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category_id, oi.product_id
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY revenue DESC) AS rn
    FROM revenue
)
SELECT * FROM ranked WHERE rn <= 3;


-- ------------------------------------------------------------
-- PROBLEM 18: Products never sold.
-- ------------------------------------------------------------
SELECT p.product_id, p.product_name
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;


-- ------------------------------------------------------------
-- PROBLEM 19: Pair of products most often bought together (basket analysis).
-- Approach: self-join order_items on order_id with product_id ordering.
-- ------------------------------------------------------------
SELECT a.product_id AS product_a, b.product_id AS product_b, COUNT(*) AS pair_count
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.product_id < b.product_id
GROUP BY a.product_id, b.product_id
ORDER BY pair_count DESC
FETCH FIRST 10 ROWS ONLY;


-- ------------------------------------------------------------
-- PROBLEM 20: Year-over-year revenue growth per month.
-- ------------------------------------------------------------
WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS m, SUM(amount) AS revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT m, revenue,
       LAG(revenue, 12) OVER (ORDER BY m) AS revenue_last_year,
       100.0 * (revenue - LAG(revenue, 12) OVER (ORDER BY m))
            / NULLIF(LAG(revenue, 12) OVER (ORDER BY m), 0) AS yoy_pct
FROM monthly;


-- ------------------------------------------------------------
-- PROBLEM 21: Median order amount per customer.
-- Approach: PERCENTILE_CONT.
-- ------------------------------------------------------------
SELECT customer_id,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_amount
FROM orders
GROUP BY customer_id;


-- ------------------------------------------------------------
-- PROBLEM 22: Cumulative distribution of order amounts.
-- ------------------------------------------------------------
SELECT order_id, amount, CUME_DIST() OVER (ORDER BY amount) AS cd
FROM orders;


-- ------------------------------------------------------------
-- PROBLEM 23: Top 10% spenders.
-- Approach: NTILE(10) and pick bucket 1 (highest).
-- ------------------------------------------------------------
WITH spend AS (
    SELECT customer_id, SUM(amount) AS total
    FROM orders
    GROUP BY customer_id
), bucketed AS (
    SELECT *, NTILE(10) OVER (ORDER BY total DESC) AS decile
    FROM spend
)
SELECT * FROM bucketed WHERE decile = 1;


-- ------------------------------------------------------------
-- PROBLEM 24: First touch attribution: first product bought by each customer.
-- ------------------------------------------------------------
WITH ranked AS (
    SELECT oi.product_id, o.customer_id, o.order_date,
           ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date, o.order_id) AS rn
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
)
SELECT customer_id, product_id, order_date
FROM ranked
WHERE rn = 1;


-- ------------------------------------------------------------
-- PROBLEM 25: Cohort retention: % of cohort active each subsequent month.
-- ------------------------------------------------------------
WITH cm AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS order_month
    FROM orders
), first_m AS (
    SELECT customer_id, MIN(order_month) AS cohort_month FROM cm GROUP BY customer_id
), joined AS (
    SELECT f.cohort_month, c.order_month, c.customer_id
    FROM cm c JOIN first_m f ON c.customer_id = f.customer_id
), cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_total
    FROM first_m GROUP BY cohort_month
)
SELECT j.cohort_month, j.order_month,
       COUNT(DISTINCT j.customer_id) AS active_customers,
       100.0 * COUNT(DISTINCT j.customer_id) / cs.cohort_total AS retention_pct
FROM joined j
JOIN cohort_size cs ON j.cohort_month = cs.cohort_month
GROUP BY j.cohort_month, j.order_month, cs.cohort_total
ORDER BY j.cohort_month, j.order_month;


-- ------------------------------------------------------------
-- PROBLEM 26: Sessionize logins with 30-minute inactivity gap.
-- ------------------------------------------------------------
WITH flagged AS (
    SELECT user_id, login_time,
           CASE
             WHEN login_time - LAG(login_time) OVER (PARTITION BY user_id ORDER BY login_time)
                  > INTERVAL '30 minutes' OR LAG(login_time) OVER (PARTITION BY user_id ORDER BY login_time) IS NULL
             THEN 1 ELSE 0 END AS is_new_session
    FROM logins
), sessions AS (
    SELECT user_id, login_time,
           SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY login_time) AS session_id
    FROM flagged
)
SELECT user_id, session_id,
       MIN(login_time) AS session_start, MAX(login_time) AS session_end,
       COUNT(*) AS events
FROM sessions
GROUP BY user_id, session_id;


-- ------------------------------------------------------------
-- PROBLEM 27: Consecutive login streak per user (islands).
-- ------------------------------------------------------------
WITH d AS (
    SELECT DISTINCT user_id, login_time::date AS d FROM logins
), grouped AS (
    SELECT user_id, d,
           d - INTERVAL '1 day' * ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d) AS grp
    FROM d
)
SELECT user_id, MIN(d) AS streak_start, MAX(d) AS streak_end, COUNT(*) AS streak_len
FROM grouped
GROUP BY user_id, grp;


-- ------------------------------------------------------------
-- PROBLEM 28: Find gaps (missing dates) in daily orders.
-- ------------------------------------------------------------
WITH dates AS (
    SELECT generate_series(MIN(order_date), MAX(order_date), INTERVAL '1 day')::date AS d FROM orders
)
SELECT d FROM dates
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.order_date::date = d);


-- ------------------------------------------------------------
-- PROBLEM 29: Recursive employee hierarchy with level and path.
-- ------------------------------------------------------------
WITH RECURSIVE h AS (
    SELECT employee_id, manager_id, employee_name, 1 AS lvl, employee_name::text AS path
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.employee_id, e.manager_id, e.employee_name, h.lvl + 1, h.path || ' > ' || e.employee_name
    FROM employees e JOIN h ON e.manager_id = h.employee_id
)
SELECT * FROM h ORDER BY lvl, employee_id;


-- ------------------------------------------------------------
-- PROBLEM 30: Count direct + indirect reports per manager.
-- ------------------------------------------------------------
WITH RECURSIVE reports AS (
    SELECT employee_id AS manager_id, employee_id AS report_id FROM employees
    UNION ALL
    SELECT r.manager_id, e.employee_id
    FROM reports r JOIN employees e ON e.manager_id = r.report_id
)
SELECT manager_id, COUNT(*) - 1 AS total_reports
FROM reports
GROUP BY manager_id;


-- ------------------------------------------------------------
-- PROBLEM 31: Overlapping subscription detection.
-- ------------------------------------------------------------
SELECT a.customer_id, a.subscription_id, b.subscription_id
FROM subscriptions a
JOIN subscriptions b ON a.customer_id = b.customer_id
                    AND a.subscription_id < b.subscription_id
                    AND a.start_date <= b.end_date
                    AND b.start_date <= a.end_date;


-- ------------------------------------------------------------
-- PROBLEM 32: Latest status per order (CDC-style).
-- ------------------------------------------------------------
SELECT *
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
    FROM order_status_history
) t
WHERE rn = 1;


-- ------------------------------------------------------------
-- PROBLEM 33: SCD Type 2 insert pattern for changed dimension rows.
-- ------------------------------------------------------------
-- Step A: expire current rows where attributes changed.
UPDATE dim_customer d
SET valid_to = CURRENT_DATE, is_current = FALSE
FROM staging_customer s
WHERE d.customer_id = s.customer_id
  AND d.is_current = TRUE
  AND (d.city <> s.city OR d.email <> s.email);

-- Step B: insert new versions.
INSERT INTO dim_customer (customer_id, name, city, email, valid_from, valid_to, is_current)
SELECT s.customer_id, s.name, s.city, s.email, CURRENT_DATE, NULL, TRUE
FROM staging_customer s
LEFT JOIN dim_customer d
  ON d.customer_id = s.customer_id AND d.is_current = TRUE
WHERE d.customer_id IS NULL
   OR d.city <> s.city OR d.email <> s.email;


-- ------------------------------------------------------------
-- PROBLEM 34: Fraud detection - >5 transactions within 1 minute.
-- ------------------------------------------------------------
SELECT customer_id, txn_time,
       COUNT(*) OVER (PARTITION BY customer_id ORDER BY txn_time
                      RANGE BETWEEN INTERVAL '1 minute' PRECEDING AND CURRENT ROW) AS recent_txns
FROM transactions
QUALIFY recent_txns > 5;  -- Snowflake/BigQuery; otherwise wrap in subquery


-- ------------------------------------------------------------
-- PROBLEM 35: Detect price drops compared to previous price.
-- ------------------------------------------------------------
SELECT product_id, change_date, price,
       LAG(price) OVER (PARTITION BY product_id ORDER BY change_date) AS prev_price
FROM product_prices
WHERE price < LAG(price) OVER (PARTITION BY product_id ORDER BY change_date);


-- ------------------------------------------------------------
-- PROBLEM 36: Funnel conversion: signup -> first_order -> repeat_order.
-- ------------------------------------------------------------
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS fo FROM orders GROUP BY customer_id
), repeat_order AS (
    SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) >= 2
)
SELECT
    COUNT(*) AS signups,
    COUNT(fo.customer_id) AS converted_first_order,
    COUNT(r.customer_id) AS converted_repeat
FROM customers c
LEFT JOIN first_order fo ON c.customer_id = fo.customer_id
LEFT JOIN repeat_order r ON c.customer_id = r.customer_id;


-- ------------------------------------------------------------
-- PROBLEM 37: Average order amount by customer status segment.
-- ------------------------------------------------------------
SELECT c.status, AVG(o.amount) AS avg_order
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.status;


-- ------------------------------------------------------------
-- PROBLEM 38: Find duplicate orders (same customer, same amount, same day).
-- ------------------------------------------------------------
SELECT customer_id, order_date, amount, COUNT(*) AS cnt
FROM orders
GROUP BY customer_id, order_date, amount
HAVING COUNT(*) > 1;


-- ------------------------------------------------------------
-- PROBLEM 39: Conditional aggregation - count by status in one row.
-- ------------------------------------------------------------
SELECT
    SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END) AS paid_count,
    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_count
FROM orders;


-- ------------------------------------------------------------
-- PROBLEM 40: Find customers whose total spend > 2x average spend.
-- ------------------------------------------------------------
WITH t AS (
    SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id
)
SELECT * FROM t WHERE total > 2 * (SELECT AVG(total) FROM t);


-- ------------------------------------------------------------
-- PROBLEM 41: Compute Average Order Value (AOV) by month.
-- ------------------------------------------------------------
SELECT DATE_TRUNC('month', order_date) AS m,
       SUM(amount) / NULLIF(COUNT(*), 0) AS aov
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY m;


-- ------------------------------------------------------------
-- PROBLEM 42: Compute Customer Lifetime Value (basic).
-- ------------------------------------------------------------
SELECT customer_id, SUM(amount) AS clv,
       MIN(order_date) AS first_order,
       MAX(order_date) AS last_order,
       MAX(order_date) - MIN(order_date) AS lifespan_days
FROM orders
GROUP BY customer_id;


-- ------------------------------------------------------------
-- PROBLEM 43: Anti-join - customers in CRM but not in orders.
-- ------------------------------------------------------------
SELECT c.*
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;


-- ------------------------------------------------------------
-- PROBLEM 44: Rank products globally and within category.
-- ------------------------------------------------------------
SELECT product_id, category_id, revenue,
       RANK() OVER (ORDER BY revenue DESC) AS global_rank,
       RANK() OVER (PARTITION BY category_id ORDER BY revenue DESC) AS category_rank
FROM (
    SELECT oi.product_id, p.category_id, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
    GROUP BY oi.product_id, p.category_id
) t;


-- ------------------------------------------------------------
-- PROBLEM 45: Compute weekly active users (WAU).
-- ------------------------------------------------------------
SELECT DATE_TRUNC('week', login_time) AS week_start,
       COUNT(DISTINCT user_id) AS wau
FROM logins
GROUP BY DATE_TRUNC('week', login_time)
ORDER BY week_start;


-- ------------------------------------------------------------
-- PROBLEM 46: Compute Daily Active Users / Monthly Active Users ratio (stickiness).
-- ------------------------------------------------------------
WITH d AS (
    SELECT login_time::date AS d, COUNT(DISTINCT user_id) AS dau FROM logins GROUP BY 1
), m AS (
    SELECT DATE_TRUNC('month', login_time)::date AS m, COUNT(DISTINCT user_id) AS mau FROM logins GROUP BY 1
)
SELECT d.d, d.dau, m.mau, 1.0 * d.dau / NULLIF(m.mau, 0) AS stickiness
FROM d JOIN m ON DATE_TRUNC('month', d.d) = m.m;


-- ------------------------------------------------------------
-- PROBLEM 47: Find customers who bought product A but not product B.
-- ------------------------------------------------------------
SELECT DISTINCT o.customer_id
FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.product_id = 'A'
  AND o.customer_id NOT IN (
    SELECT o2.customer_id FROM orders o2 JOIN order_items oi2 ON o2.order_id = oi2.order_id WHERE oi2.product_id = 'B'
  );


-- ------------------------------------------------------------
-- PROBLEM 48: String parsing - extract domain from email.
-- ------------------------------------------------------------
SELECT customer_id, email, SPLIT_PART(email, '@', 2) AS domain
FROM customers
WHERE email IS NOT NULL;


-- ------------------------------------------------------------
-- PROBLEM 49: JSON column parsing (PostgreSQL/Snowflake style).
-- ------------------------------------------------------------
-- PostgreSQL
SELECT event_id, payload->>'user_id' AS user_id, (payload->>'amount')::numeric AS amount
FROM events;

-- Snowflake
-- SELECT event_id, payload:user_id::string AS user_id, payload:amount::number AS amount FROM events;


-- ------------------------------------------------------------
-- PROBLEM 50: Compute query plan visibility - check long-running queries.
-- (Postgres dictionary example.)
-- ------------------------------------------------------------
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity
WHERE state <> 'idle'
ORDER BY duration DESC;
