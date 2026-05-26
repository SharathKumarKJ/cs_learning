-- SQL JOIN basics

-- 1. INNER JOIN customers and orders.
SELECT c.customer_id, c.customer_name, o.order_id, o.amount
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id;

-- 2. LEFT JOIN to keep all customers.
SELECT c.customer_id, c.customer_name, o.order_id
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id;

-- 3. RIGHT JOIN example.
SELECT c.customer_name, o.order_id
FROM customers c
RIGHT JOIN orders o ON c.customer_id = o.customer_id;

-- 4. FULL OUTER JOIN.
SELECT c.customer_id, o.order_id
FROM customers c
FULL OUTER JOIN orders o ON c.customer_id = o.customer_id;

-- 5. SELF JOIN: find employees and their managers.
SELECT e.employee_name, m.employee_name AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;

-- 6. CROSS JOIN: all combinations.
SELECT p.product_id, c.color_id
FROM products p
CROSS JOIN colors c;
