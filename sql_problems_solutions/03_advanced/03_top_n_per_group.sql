-- Top N per group

-- 1. Top 3 products by revenue per category.
WITH ranked AS (
    SELECT category_id, product_id, SUM(amount) AS revenue,
           ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY SUM(amount) DESC) AS rn
    FROM order_items
    GROUP BY category_id, product_id
)
SELECT *
FROM ranked
WHERE rn <= 3;

-- 2. Nth highest salary per department.
WITH ranked AS (
    SELECT department_id, employee_id, salary,
           DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rk
    FROM employees
)
SELECT * FROM ranked WHERE rk = 3;
