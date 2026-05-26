-- Very Advanced SQL Problems and Solutions

-- 1. Sessionize events using 30-minute inactivity gap.
WITH ordered_events AS (
    SELECT user_id, event_time,
           CASE
               WHEN LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) IS NULL THEN 1
               WHEN event_time - LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) > INTERVAL '30 minutes' THEN 1
               ELSE 0
           END AS new_session_flag
    FROM events
), sessionized AS (
    SELECT user_id, event_time,
           SUM(new_session_flag) OVER (PARTITION BY user_id ORDER BY event_time) AS session_number
    FROM ordered_events
)
SELECT user_id, session_number, MIN(event_time) AS session_start, MAX(event_time) AS session_end, COUNT(*) AS event_count
FROM sessionized
GROUP BY user_id, session_number;

-- 2. Recursive employee hierarchy.
WITH RECURSIVE hierarchy AS (
    SELECT employee_id, manager_id, employee_name, 1 AS level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.employee_id, e.manager_id, e.employee_name, h.level + 1
    FROM employees e
    JOIN hierarchy h ON e.manager_id = h.employee_id
)
SELECT *
FROM hierarchy
ORDER BY level, employee_id;

-- 3. Detect overlapping subscriptions.
SELECT a.customer_id, a.subscription_id AS subscription_a, b.subscription_id AS subscription_b
FROM subscriptions a
JOIN subscriptions b
  ON a.customer_id = b.customer_id
 AND a.subscription_id < b.subscription_id
 AND a.start_date <= b.end_date
 AND b.start_date <= a.end_date;

-- 4. Percentile-based outlier detection.
WITH stats AS (
    SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount) AS q1,
           PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) AS q3
    FROM orders
), bounds AS (
    SELECT q1, q3, q1 - 1.5 * (q3 - q1) AS lower_bound, q3 + 1.5 * (q3 - q1) AS upper_bound
    FROM stats
)
SELECT o.*
FROM orders o
CROSS JOIN bounds b
WHERE o.amount < b.lower_bound OR o.amount > b.upper_bound;

-- 5. Merge CDC events to get latest state.
WITH ranked_cdc AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY event_time DESC, event_sequence DESC) AS rn
    FROM cdc_events
)
SELECT entity_id, col1, col2, operation, event_time
FROM ranked_cdc
WHERE rn = 1 AND operation <> 'DELETE';
