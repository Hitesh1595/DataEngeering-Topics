# Actions vs Transformations (Spark)

## Transformations
Build the DAG, **lazy** — don't execute until an action triggers them. Return a new RDD/DataFrame.

**Narrow** (no shuffle, one input partition → one output partition):
- `map`, `filter`, `select`, `withColumn`, `union`

**Wide** (shuffle required, data moves across partitions):
- `groupBy`, `join`, `distinct`, `orderBy`, `repartition`

```python
df2 = df.filter(df.age > 18)      # narrow, lazy — nothing runs yet
df3 = df2.groupBy("city").count() # wide, lazy — still nothing runs
```

## Actions
**Trigger execution** of the whole DAG built so far. Return a result (not another DataFrame) or write output.

- `count()`, `collect()`, `show()`, `take(n)`, `first()`, `write.parquet(...)`, `write.csv(...)`

```python
df3.show()   # action — runs entire DAG: filter → groupBy → count
```

## Why Lazy Evaluation
Spark builds full DAG first, then optimizes whole plan (via Catalyst) before running — avoids redundant work, combines steps, picks best execution strategy. Nothing computed until an action forces it.

## Quick Table

| | Transformations | Actions |
|---|---|---|
| Execution | Lazy (builds DAG) | Eager (triggers DAG run) |
| Returns | New RDD/DataFrame | Value, or writes output |
| Examples | `map`, `filter`, `join`, `groupBy` | `count`, `collect`, `show`, `write` |
| Cost | Free (just plan) | Where actual compute happens |

## Interview Q&A
**Q: Why does Spark use lazy evaluation?**
A: Lets Spark optimize the entire chain of transformations as one plan before executing — avoids unnecessary passes over data, better performance than eager execution.

**Q: If I call `df.filter(...)` and nothing happens, why?**
A: Filter is a transformation — lazy. Nothing runs until an action (`show`, `count`, `write`, etc.) is called.

**Q: `collect()` vs `show()`?**
A: Both actions. `collect()` pulls all rows to driver as a list (risk of OOM on large data). `show()` prints a preview (default 20 rows) without pulling full dataset to driver.

**Q: Is `count()` expensive?**
A: Triggers full execution of DAG up to that point — reads all data, applies all transformations, then counts. Not free even though it just returns a number.
