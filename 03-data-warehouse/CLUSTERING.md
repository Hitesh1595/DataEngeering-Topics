# Clustering in BigQuery

## What is Clustering

Physically sorting and co-locating rows within each partition based on the values of one or more columns. BigQuery stores related rows together on disk so queries that filter on cluster columns scan less data.

```
yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID, PULocationID

Within each date partition, rows are sorted by VendorID → PULocationID
┌─────────────────────────────────────┐
│ Partition: 2019-01-01               │
│   VendorID=1, PULocationID=1  ──┐   │
│   VendorID=1, PULocationID=1    │   │  ← co-located
│   VendorID=1, PULocationID=2  ──┘   │
│   VendorID=2, PULocationID=5  ──┐   │
│   VendorID=2, PULocationID=5    │   │  ← co-located
└─────────────────────────────────────┘
```

A query filtering `WHERE VendorID = 1` skips the VendorID=2 blocks entirely.

---

## Syntax

```sql
CREATE TABLE yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID, PULocationID, DOLocationID;
```

Up to **4 cluster columns** allowed. Order matters — first column has the most impact.

---

## Partitioning vs Clustering

| | Partitioning | Clustering |
|--|-------------|------------|
| Works on | One column | Up to 4 columns |
| Granularity | Whole segments (date/range) | Row-level sorting within partition |
| Cost estimate | Shown before query runs | Not shown upfront (BQ estimates after) |
| Best for | Date/time filters | High-cardinality filters (location, vendor) |
| Maintenance | Manual partition management | Automatic, BQ handles it |

---

## When to Use Clustering Over Partitioning

- Column has too many unique values for partitioning (e.g. location ID, user ID)
- Queries filter on multiple columns together
- Table < 1 GB — partitioning adds overhead, clustering is lighter
- You already use partitioning and want further refinement within partitions

---

## Combining Both (Best Practice)

```sql
CREATE TABLE yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime)   -- coarse filter: by day
CLUSTER BY VendorID, PULocationID;        -- fine filter: within each day
```

Query filters on both:
```sql
WHERE DATE(tpep_pickup_datetime) = '2019-01-01'  -- hits one partition
  AND VendorID = '1'                              -- hits cluster block within partition
```

Result: minimal data scanned, lowest cost.

---

## Key Points

- Clustering is **free** — no extra cost, BQ manages it automatically
- BQ **re-clusters** automatically as new data is inserted
- Most effective on columns frequently used in WHERE, JOIN, or GROUP BY
- Cluster column order should match the most common query filter order
