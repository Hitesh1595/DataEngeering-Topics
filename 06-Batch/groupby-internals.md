# How groupBy Works Internally — DAG Flow

```python
df.groupBy("PULocationID").agg(F.sum("fare_amount")).show()
```

## 3 Phases

**1. Partial aggregation (map-side)** — each executor aggregates its own partition locally first, before sending anything over network.
**2. Shuffle (Exchange)** — partial results redistributed, hash-partitioned by grouping key, so all records for same key land on one executor.
**3. Final aggregation (reduce-side)** — each executor merges the partials it received into the final per-key result.

```
Partition 1                    Partition 2
[10,5] [10,3] [20,8]           [10,2] [30,4]
     │                              │
     ▼ partial agg (map-side)       ▼ partial agg (map-side)
 {10: 8, 20: 8}                 {10: 2, 30: 4}
     │                              │
     └──────────┬───────────────────┘
                 ▼
          SHUFFLE (Exchange)
     hash-partition by PULocationID
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
 key=10       key=20       key=30
 merge(8,2)   merge(8)     merge(4)
     │           │           │
     ▼           ▼           ▼
   10:10       20:8        30:4   ← final result
```

## DAG as Spark UI Shows It

```
STAGE 0 (map-side, no shuffle yet)          STAGE 1 (reduce-side, after shuffle)
┌─────────────────────────────┐             ┌──────────────────────────────┐
│ Scan parquet                │             │ Exchange (shuffle read)      │
│   │                         │   shuffle   │   │                          │
│   ▼                         │   write     │   ▼                          │
│ HashAggregate (partial_sum) │ ──────────▶ │ HashAggregate (final sum)    │
└─────────────────────────────┘             │   │                          │
                                             │   ▼                          │
                                             │ Result → show()/collect()    │
                                             └──────────────────────────────┘
```

- **Stage boundary = shuffle.** One job, split into 2 stages because of the Exchange.
- Stage 0 tasks = number of input partitions. Stage 1 tasks = `spark.sql.shuffle.partitions` (default 200).

## Shuffle Internals: Sort-Based Merge

Spark's default shuffle manager (since 1.2, "sort" shuffle) doesn't just throw bytes over the network — on the write side it **sorts each partition's records by target partition ID** (and spills to disk in sorted runs if data doesn't fit memory), writing one sorted, indexed file per map task. On the read side, each reduce task does a **k-way merge** of the sorted segments it needs from every map output — same merge-sort idea as external sort, applied to combine shuffle data efficiently without loading everything into memory at once.

```
Map task output (sorted by partition key) → spill runs → merge into one sorted file
                                                          │
Reduce task: merge-reads its slice from every map's sorted file (k-way merge)
```

This is why grouping/joining huge datasets is disk + CPU heavy even after map-side pre-aggregation — the sort/merge itself costs time, separate from the network transfer.

## HashAggregate vs SortAggregate

Spark picks the aggregate strategy per stage:
- **HashAggregate** (default, faster) — builds an in-memory hash map keyed by group columns. Used when the aggregate/group-by types support it.
- **SortAggregate** (fallback) — used when data types aren't hashable in Spark's hash map implementation (e.g. certain complex types), or when forced via config. Sorts rows by group key first, then aggregates adjacent matching rows — classic merge-sort-style grouping, like SQL's `GROUP BY` over a sorted index.

```
HashAggregate: unsorted input → hash map {key: running_agg} → emit per key
SortAggregate: sort input by key → scan once, aggregate consecutive matching rows → emit
```

**SortMergeJoin** (related, common follow-up) — Spark's default join strategy for large tables: both sides shuffled + **sorted by join key**, then merged like a zip — walk both sorted streams together, matching keys align without a hash table. Same merge-sort principle as shuffle read above.

## Physical Plan (same thing, as `.explain()` prints it)

```python
df.groupBy("PULocationID").agg(F.sum("fare_amount")).explain()
```
```
*(2) HashAggregate(keys=[PULocationID], functions=[sum(fare_amount)])
+- Exchange hashpartitioning(PULocationID, 200)
   +- *(1) HashAggregate(keys=[PULocationID], functions=[partial_sum(fare_amount)])
      +- *(1) Scan parquet ...
```
Read bottom-up: scan → partial hash aggregate (map-side) → exchange (shuffle) → final hash aggregate (reduce-side). Matches the DAG above exactly.

## Where to See It Live
Run the job, keep SparkSession alive, open `http://localhost:4040`:
- **Jobs tab** → click the job triggered by `.show()`.
- **DAG Visualization** (inside that job) → renders the two boxes above visually, with the Exchange node between them.
- **Stages tab** → click each stage → **Shuffle Write** (Stage 0) and **Shuffle Read** (Stage 1) metrics show exactly how much data crossed the network.
- **SQL tab** → shows the physical plan tree above.

## Interview Q&A

**Q: Does groupBy shuffle all raw data?**
A: No — partial/map-side aggregation reduces data per partition first; only the reduced partials get shuffled, not raw rows.

**Q: Why 2 stages for one groupBy?**
A: Shuffle always creates a stage boundary. Stage 0 = local partial aggregation (narrow). Stage 1 = merge partials per key after shuffle (needs data from all partitions).

**Q: What's the role of merge sort in a Spark shuffle?**
A: Shuffle writer sorts each map task's output by partition key (spilling sorted runs to disk if needed); shuffle reader does a k-way merge of the sorted segments it needs across all map outputs. Same mechanism also backs `SortAggregate` and `SortMergeJoin`.

**Q: HashAggregate vs SortAggregate — which is faster?**
A: HashAggregate usually faster (single pass, in-memory hash map). SortAggregate is the fallback when types aren't hash-compatible, or data is already sorted/too large for a hash map — costs an explicit sort first.

**Q: How do you check shuffle cost without opening Spark UI?**
A: `.explain()` for the plan; or Spark UI Stages tab for actual Shuffle Read/Write byte counts at runtime.

**Q: What controls task count in the reduce-side stage?**
A: `spark.sql.shuffle.partitions` (default 200) — tune down for small data (less overhead), up for very large data (avoid huge skewed tasks).
