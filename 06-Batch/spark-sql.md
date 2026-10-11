# Spark SQL — Interview Notes

Run SQL queries directly on DataFrames via `spark.sql()` — same Catalyst optimizer as DataFrame API, just different syntax. Pick whichever's more readable for the task; performance is identical.

## Registering a DataFrame as SQL-queryable

```python
df = spark.read.parquet("data/fhvhv")

# temp view — scoped to this SparkSession only
df.createOrReplaceTempView("trips")

# global temp view — shared across sessions in same Spark application
df.createOrReplaceGlobalTempView("trips")
# query global view with global_temp. prefix
spark.sql("SELECT * FROM global_temp.trips LIMIT 5").show()

# registerTempTable — older/deprecated API (pre Spark 2.0 naming), same effect as createOrReplaceTempView
df.registerTempTable("trips")
```
**Note:** `registerTempTable` deprecated since Spark 2.0 — use `createOrReplaceTempView` instead. Still works (kept for backward compat), may show up in older codebases/interview questions.

## Basic Query

```python
spark.sql("""
    SELECT PULocationID, COUNT(*) AS trip_count
    FROM trips
    WHERE trip_distance > 1
    GROUP BY PULocationID
    ORDER BY trip_count DESC
    LIMIT 10
""").show()
```

Equivalent DataFrame API:
```python
from pyspark.sql import functions as F

(df.filter(F.col("trip_distance") > 1)
   .groupBy("PULocationID")
   .agg(F.count("*").alias("trip_count"))
   .orderBy(F.col("trip_count").desc())
   .limit(10)
   .show())
```

## Joins in Spark SQL

```python
pickups.createOrReplaceTempView("pickups")
zones.createOrReplaceTempView("zones")

spark.sql("""
    SELECT z.Zone, COUNT(*) AS trips
    FROM pickups p
    JOIN zones z ON p.PULocationID = z.LocationID
    GROUP BY z.Zone
    ORDER BY trips DESC
""").show()
```

## Window Functions (common interview topic)

```python
spark.sql("""
    SELECT
        PULocationID,
        pickup_datetime,
        trip_distance,
        RANK() OVER (PARTITION BY PULocationID ORDER BY trip_distance DESC) AS rank_in_zone,
        AVG(trip_distance) OVER (PARTITION BY PULocationID) AS avg_distance_zone
    FROM trips
""").show()
```

Equivalent DataFrame API:
```python
from pyspark.sql.window import Window

w = Window.partitionBy("PULocationID").orderBy(F.col("trip_distance").desc())
w_all = Window.partitionBy("PULocationID")

df.select(
    "PULocationID", "pickup_datetime", "trip_distance",
    F.rank().over(w).alias("rank_in_zone"),
    F.avg("trip_distance").over(w_all).alias("avg_distance_zone")
).show()
```

## CTE (Common Table Expression)

```python
spark.sql("""
    WITH high_value_trips AS (
        SELECT * FROM trips WHERE total_amount > 50
    )
    SELECT PULocationID, COUNT(*) AS cnt
    FROM high_value_trips
    GROUP BY PULocationID
""").show()
```

## Running SQL Scripts / Multiple Statements

```python
spark.sql("CREATE OR REPLACE TEMP VIEW filtered AS SELECT * FROM trips WHERE trip_distance > 0")
result = spark.sql("SELECT COUNT(*) FROM filtered")
```

## Catalog — Inspect Registered Tables/Views

```python
spark.catalog.listTables()
spark.catalog.listColumns("trips")
spark.sql("SHOW TABLES").show()
spark.sql("DESCRIBE trips").show()
```

## Interview Q&A

**Q: `spark.sql()` vs DataFrame API — which is faster?**
A: Neither — both compile down to the same Catalyst logical plan, same physical execution. Choice is style/readability, not performance.

**Q: Temp view vs global temp view?**
A: Temp view scoped to current `SparkSession` only. Global temp view shared across all sessions within the same Spark application, stored in `global_temp` database, needs `global_temp.` prefix to query.

**Q: Does `createOrReplaceTempView` persist data to disk?**
A: No — it's just a named reference to the DataFrame's logical plan, not materialized storage. Gone when the Spark application/session ends.

**Q: How do window functions differ from `groupBy`?**
A: `groupBy` collapses rows into one row per group. Window functions (`OVER (PARTITION BY ...)`) compute aggregates/ranks per row while keeping all original rows — row stays, extra column added.

**Q: Can you mix SQL and DataFrame API in the same pipeline?**
A: Yes — `spark.sql(...)` returns a DataFrame, so you can chain `.filter()`, `.join()`, etc. on the result, and vice versa (register a DataFrame as a view, then query it with SQL).
