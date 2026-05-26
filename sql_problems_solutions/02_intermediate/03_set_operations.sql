-- Set operations

-- 1. UNION removes duplicates.
SELECT customer_id FROM orders_jan
UNION
SELECT customer_id FROM orders_feb;

-- 2. UNION ALL keeps duplicates (faster).
SELECT customer_id FROM orders_jan
UNION ALL
SELECT customer_id FROM orders_feb;

-- 3. INTERSECT: customers in both months.
SELECT customer_id FROM orders_jan
INTERSECT
SELECT customer_id FROM orders_feb;

-- 4. EXCEPT/MINUS: in Jan but not Feb (churned).
SELECT customer_id FROM orders_jan
EXCEPT
SELECT customer_id FROM orders_feb;
