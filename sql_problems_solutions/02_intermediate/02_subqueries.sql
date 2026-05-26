-- Subqueries

-- 1. Customers who spent more than average.
SELECT customer_id, SUM(amount) AS total
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > (SELECT AVG(total) FROM (SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id) sub);

-- 2. Correlated subquery: orders above customer average.
SELECT *
FROM orders o
WHERE amount > (SELECT AVG(amount) FROM orders o2 WHERE o2.customer_id = o.customer_id);

-- 3. EXISTS check.
SELECT c.*
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);

-- 4. NOT IN vs NOT EXISTS (NOT EXISTS handles NULLs safely).
SELECT c.*
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);
