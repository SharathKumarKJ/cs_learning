-- Intermediate SQL Problems and Solutions

-- 1. Total sales by customer.
SELECT c.customer_id, c.customer_name, SUM(o.amount) AS total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name;

-- 2. Customers without orders.
SELECT c.customer_id, c.customer_name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;

-- 3. Top 5 customers by sales.
SELECT c.customer_id, c.customer_name, SUM(o.amount) AS total_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_amount DESC
FETCH FIRST 5 ROWS ONLY;

-- 4. Monthly sales.
SELECT DATE_TRUNC('month', order_date) AS sales_month, SUM(amount) AS total_amount
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY sales_month;

-- 5. Products never sold.
SELECT p.product_id, p.product_name
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.product_id IS NULL;

-- 6. Duplicate email detection.
SELECT email, COUNT(*) AS duplicate_count
FROM customers
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1;

-- 7. Orders above customer average.
SELECT o.*
FROM orders o
WHERE o.amount > (
    SELECT AVG(o2.amount)
    FROM orders o2
    WHERE o2.customer_id = o.customer_id
);

-- 8. Customer first order date.
SELECT customer_id, MIN(order_date) AS first_order_date
FROM orders
GROUP BY customer_id;
