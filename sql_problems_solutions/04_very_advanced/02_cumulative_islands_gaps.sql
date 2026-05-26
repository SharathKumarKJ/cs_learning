-- Islands and gaps problems

-- 1. Consecutive login streaks per user.
WITH dated AS (
    SELECT user_id, login_date,
           login_date - INTERVAL '1 day' * ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS grp
    FROM logins
)
SELECT user_id, MIN(login_date) AS streak_start, MAX(login_date) AS streak_end, COUNT(*) AS streak_length
FROM dated
GROUP BY user_id, grp
ORDER BY user_id, streak_start;

-- 2. Find missing dates (gaps).
WITH all_dates AS (
    SELECT generate_series(MIN(order_date), MAX(order_date), INTERVAL '1 day')::date AS d
    FROM orders
)
SELECT d FROM all_dates
WHERE d NOT IN (SELECT DISTINCT order_date::date FROM orders);
