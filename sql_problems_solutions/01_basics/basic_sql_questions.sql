-- Basic SQL Problems and Solutions

-- 1. Select all customers.
SELECT *
FROM customers;

-- 2. Select active customers only.
SELECT customer_id, customer_name, city
FROM customers
WHERE status = 'ACTIVE';

-- 3. Count total orders.
SELECT COUNT(*) AS total_orders
FROM orders;

-- 4. Find total sales amount.
SELECT SUM(amount) AS total_sales
FROM orders;

-- 5. Find orders placed after a date.
SELECT order_id, customer_id, order_date, amount
FROM orders
WHERE order_date >= DATE '2026-01-01';

-- 6. Get unique customer cities.
SELECT DISTINCT city
FROM customers;

-- 7. Sort customers by name.
SELECT customer_id, customer_name
FROM customers
ORDER BY customer_name;

-- 8. Find customers with missing email.
SELECT customer_id, customer_name
FROM customers
WHERE email IS NULL;

-- 9. Count customers by city.
SELECT city, COUNT(*) AS customer_count
FROM customers
GROUP BY city;

-- 10. Find average order amount.
SELECT AVG(amount) AS average_order_amount
FROM orders;
