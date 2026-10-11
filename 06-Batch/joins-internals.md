# Joins — Internal Working (PySpark)

```python
trips.join(zones, trips.PULocationID == zones.LocationID, "inner")
```

Spark picks one of several physical join strategies based on table size, join type, and config — visible via `.explain()`.

## 1. Broadcast Hash Join (small table fits in memory)

Small side (e.g. `zones`, a few MB) sent **whole** to every executor — no shuffle of the big table needed at all.

```
Driver broadcasts small table to all executors
                 │
   ┌─────────────┼─────────────┐
   ▼             ▼             ▼
Executor 1    Executor 2    Executor 3
[big table    [big table    [big table
 partition]    partition]    partition]
   +               +             +
[full small   [full small   [full small
 table copy]   table copy]   table copy]
   │             │             │
   ▼             ▼             ▼
local hash join, no shuffle of big table
```

- Big table stays where it is — read once, no shuffle.
- Small table broadcast via driver, cached in memory on each executor as a hash map keyed on join column.
- Fastest join when applicable — avoids the expensive shuffle entirely.
- Triggered automatically when small side < `spark.sql.autoBroadcastJoinThreshold` (default 10MB), or forced via `F.broadcast(df)`.

```python
from pyspark.sql import functions as F
trips.join(F.broadcast(zones), trips.PULocationID == zones.LocationID)
```

## 2. Shuffle Hash Join (both sides shuffled, one side small enough to hash)

Both tables shuffled (hash-partitioned by join key) so matching keys land on same executor, then smaller side built into an in-memory hash map per partition, bigger side streamed through probing that hash map.

```
Table A ──shuffle──┐          Table B ──shuffle──┐
(hash by key)       ▼          (hash by key)      ▼
              same executor gets both sides' matching-key partitions
                         │
         build hash map from smaller side's partition
                         │
         stream larger side's partition, probe hash map
                         │
                    matched rows out
```

Used when neither side fits broadcast threshold, but one side still small enough to build a hash map per partition without spilling.

## 3. Sort-Merge Join (default for large ⋈ large)

Both sides shuffled **and sorted** by join key, then merged like a zipper — walk both sorted streams together, matching keys align without any hash table.

```
Table A (shuffled)         Table B (shuffled)
   sort by key                sort by key
       │                          │
   [1,2,2,3,5]                [1,2,4,5,5]
       │                          │
       └──────────┬───────────────┘
                   ▼
          merge-walk both streams:
          key=1 → match, emit
          key=2 → match (2 rows A × 1 row B), emit
          key=3 → no match in B, skip (inner join)
          key=4 → no match in A, skip
          key=5 → match (1×2), emit
```

- No hash map needed in memory — relies on sort order, scales to huge data even when neither side fits in memory.
- Cost: both shuffle AND sort on both sides — most expensive per-byte, but most scalable (no OOM risk from building a big hash map).
- Default strategy in Spark for large-large equi-joins (`spark.sql.join.preferSortMergeJoin = true`).

## 4. Broadcast Nested Loop Join / Cartesian (no join key / non-equi join)

No equality condition (`<`, `>`, cross join) → no hash/sort shortcut possible. One side broadcast (if small) or full cartesian product computed — every row of A compared against every row of B. Expensive, avoid unless truly needed.

## Comparison Table

| Strategy | Shuffle? | Memory structure | Best when |
|---|---|---|---|
| Broadcast Hash | No (big side untouched) | Hash map (small side) | One side tiny (< threshold) |
| Shuffle Hash | Yes, both sides | Hash map (smaller side, per partition) | Neither broadcastable, one side moderate size |
| Sort-Merge | Yes, both sides | None (sorted streams) | Both sides large |
| Broadcast Nested Loop | Maybe (small side) | None, brute force | Non-equi join, no key to hash/sort |

## How to Check Which Join Spark Picked

```python
trips.join(zones, "LocationID").explain()
```
```
*(2) BroadcastHashJoin [LocationID], [LocationID], Inner, BuildRight
:- *(2) Scan parquet trips
+- BroadcastExchange HashedRelationBroadcastMode
   +- *(1) Scan parquet zones
```
or for large-large:
```
*(5) SortMergeJoin [PULocationID], [LocationID], Inner
:- *(2) Sort [PULocationID ASC]
:  +- Exchange hashpartitioning(PULocationID, 200)
+- *(4) Sort [LocationID ASC]
   +- Exchange hashpartitioning(LocationID, 200)
```

## Interview Q&A

**Q: Why is broadcast join faster?**
A: Avoids shuffling the large table entirely — only the small table moves (once, to every executor). Big table read locally, no network shuffle, no sort needed.

**Q: When does Spark avoid broadcast join even if you ask for it?**
A: If the "small" table is actually too big to fit in executor memory as a broadcast variable, forcing it causes OOM — Spark may ignore the hint or the job fails. Check actual size before forcing `F.broadcast()`.

**Q: Sort-Merge Join vs Shuffle Hash Join — why is sort-merge the default for big tables?**
A: Shuffle hash join needs the smaller side's partition to fit fully in memory as a hash map — risky at scale (skew, OOM). Sort-merge needs no in-memory hash structure, just sorted sequential scan — more memory-safe for large-large joins, trades extra sort cost for reliability.

**Q: What causes a slow/skewed join?**
A: Uneven key distribution — one key has way more rows than others, so one partition/task after shuffle does disproportionate work. Fix: salting the skewed key, broadcasting the small side if applicable, or Adaptive Query Execution (AQE) skew join optimization (Spark 3+, automatic).

**Q: What is Adaptive Query Execution's role in joins?**
A: AQE (enabled by default in Spark 3.2+) can dynamically switch a sort-merge join to a broadcast join at runtime if actual shuffled data turns out smaller than expected, and can split skewed partitions automatically — reoptimizes the physical plan mid-query using real stats instead of only estimates.
