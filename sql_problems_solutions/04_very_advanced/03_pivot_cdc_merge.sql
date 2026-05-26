-- CDC merge using SQL MERGE (Snowflake/SQL Server syntax)

MERGE INTO target t
USING (
    SELECT id, name, city, op
    FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC) AS rn
        FROM cdc_events
    )
    WHERE rn = 1
) s
ON t.id = s.id
WHEN MATCHED AND s.op = 'DELETE' THEN DELETE
WHEN MATCHED AND s.op = 'UPDATE' THEN UPDATE SET t.name = s.name, t.city = s.city
WHEN NOT MATCHED AND s.op = 'INSERT' THEN INSERT (id, name, city) VALUES (s.id, s.name, s.city);
