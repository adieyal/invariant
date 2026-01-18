SELECT "name", "total_value" FROM (SELECT "name", SUM(qty) AS "quantity", AVG(price) AS "unit_price" FROM (SELECT * FROM "analytics"."daily_sales" AS "t_sales") AS _agg GROUP BY "name") AS _proj
