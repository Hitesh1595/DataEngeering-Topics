# df.select() + withColumn() + User Defined Functions (PySpark)

## df.select()
Picks columns (or expressions) from a DataFrame — transformation, lazy.

```python
from pyspark.sql import functions as F

df.select("name", "age").show()

# with expressions
df.select(
    F.col("name"),
    F.upper(F.col("city")).alias("city_upper"),
    (F.col("salary") * 1.1).alias("salary_hiked")
).show()

# selectExpr — SQL-style string expressions
df.selectExpr("name", "age + 1 as age_next_year").show()

# select all + add one
df.select("*", (F.col("age") + 1).alias("age_plus_1")).show()
```

**Notes**
- `select` returns a new DataFrame (original untouched — immutable).
- Prefer `F.col("x")` over bare string when combining with functions/expressions.
- `selectExpr` useful when porting SQL logic quickly.
- Convention: `from pyspark.sql import functions as F`, then call everything as `F.col`, `F.when`, `F.udf`, etc. — avoids name clashes with Python builtins (`sum`, `max`, `round`) and keeps every Spark function namespaced consistently.

## df.withColumn()
Adds a new column, or replaces an existing one (same name = overwrite) — transformation, lazy. Unlike `select`, keeps all existing columns automatically.

```python
df = df.withColumn("salary_hiked", F.col("salary") * 1.1)

# replace existing column
df = df.withColumn("age", F.col("age") + 1)

# conditional column
df = df.withColumn(
    "category",
    F.when(F.col("age") < 18, "minor")
    .when(F.col("age") < 60, "adult")
    .otherwise("senior")
)

# multiple columns — withColumns (plural, Spark 3.3+) takes a dict
df = df.withColumns({
    "salary_hiked": F.col("salary") * 1.1,
    "age_plus_1": F.col("age") + 1
})
```

**`select` vs `withColumn`**
- `select` — must list every column you want to keep; drops the rest.
- `withColumn` — keeps all existing columns, adds/overwrites just the one named.
- Chaining many `withColumn` calls (one per column) is less efficient than a single `select`/`withColumns` — each call adds a projection node to the plan. Fine for a few columns; prefer `select` or `withColumns` for many at once.

## User Defined Functions (UDF)
Custom Python function registered so Spark can call it per-row inside a DataFrame/SQL expression — used when no built-in function (`pyspark.sql.functions`) covers the logic.

```python
from pyspark.sql.types import StringType

def categorize(age):
    if age < 18:
        return "minor"
    elif age < 60:
        return "adult"
    return "senior"

categorize_udf = F.udf(categorize, StringType())

df.select("name", "age", categorize_udf(F.col("age")).alias("category")).show()

# same, via withColumn — adds new column, keeps rest of df untouched
df = df.withColumn("category", categorize_udf(F.col("age")))
```

**Register for use in Spark SQL:**
```python
spark.udf.register("categorize_sql", categorize, StringType())
spark.sql("SELECT name, categorize_sql(age) AS category FROM people")
```

**Caveats (common interview point)**
- UDFs are a **black box** to Catalyst optimizer — no predicate pushdown/optimization inside the UDF logic.
- Slower than built-in functions — row-by-row Python execution, serialization overhead (Python ↔ JVM).
- **Prefer built-in `pyspark.sql.functions`** whenever possible; use UDF only when no built-in exists.
- **Pandas UDF (vectorized UDF)** — faster alternative, operates on batches via Arrow instead of row-by-row:

```python
import pandas as pd

@F.pandas_udf(StringType())
def categorize_pandas(age: pd.Series) -> pd.Series:
    return age.apply(lambda a: "minor" if a < 18 else "adult" if a < 60 else "senior")

df.select("name", categorize_pandas(F.col("age")).alias("category")).show()
```

## Interview Q&A
**Q: Why avoid UDFs when possible?**
A: They bypass Catalyst optimizer and Tungsten's codegen — each row crosses JVM↔Python boundary, serialization cost, no internal optimization. Built-in functions run natively in JVM, much faster.

**Q: UDF vs Pandas UDF?**
A: Regular UDF processes row-by-row (slow, high serialization overhead). Pandas UDF processes column batches using Apache Arrow — vectorized, much faster for large data.

**Q: `select` vs `selectExpr`?**
A: `select` takes Column objects/expressions (Python API); `selectExpr` takes SQL-like strings — same result, different syntax convenience.

**Q: `select` vs `withColumn` when adding a UDF column?**
A: `select` drops any column not explicitly listed — must repeat all columns plus the new one. `withColumn` keeps every existing column automatically, only adds/overwrites the named one. Use `withColumn` to append, `select` when also reshaping/dropping columns.
