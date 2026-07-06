# Indexing

## What is an Index

A data structure that allows the database to find rows matching a condition without scanning the entire table.

```
Without index:
SELECT * FROM trips WHERE vendor_id = 2
→ scan every row (full table scan)

With index on vendor_id:
→ jump directly to matching rows via index lookup
```

---

## How It Works (B-Tree Index)

```
Index on vendor_id:

        [2]
       /   \
    [1]     [3]
   /   \   /   \
 row1 row2 row3 row4

Query: vendor_id = 2 → traverse tree → O(log n) instead of O(n)
```

---

## OLTP (PostgreSQL) — Index Heavy

PostgreSQL uses indexes extensively because queries are row-level lookups.

```sql
-- auto-created on primary key
CREATE INDEX ON trips (trip_id);

-- manual index for frequent filter column
CREATE INDEX ON trips (vendor_id);
CREATE INDEX ON trips (pickup_datetime);

-- composite index for multi-column filters
CREATE INDEX ON trips (vendor_id, pickup_datetime);
```

**Types in PostgreSQL:**

| Type | Use case |
|------|----------|
| B-Tree | Default, equality + range queries |
| Hash | Equality only |
| GIN | Full-text search, arrays |
| BRIN | Very large tables with natural ordering (timestamps) |

---

## OLAP (BigQuery) — No Traditional Indexes

BigQuery does not use traditional indexes. Instead it uses:

| Mechanism | Purpose |
|-----------|---------|
| **Partitioning** | Coarse-grained row skipping by date/range |
| **Clustering** | Fine-grained row skipping within partitions |
| **Columnar storage** | Only reads columns referenced in query |
| **Search Indexes** | Optional, for text search on STRING columns |

BigQuery's columnar format means it already skips irrelevant columns — traditional row-level indexes would add overhead without benefit at PB scale.

---

## Columnar Storage (Why BQ Doesn't Need Indexes)

**Row storage (OLTP):**
```
Row 1: [VendorID=1, pickup=2019-01-01, fare=5.50, ...]
Row 2: [VendorID=2, pickup=2019-01-01, fare=8.00, ...]
```
Reading one column requires reading entire rows.

**Columnar storage (OLAP):**
```
VendorID col:  [1, 2, 1, 2, ...]
pickup col:    [2019-01-01, 2019-01-01, ...]
fare col:      [5.50, 8.00, ...]
```
`SELECT AVG(fare_amount)` reads only the fare column — all other columns skipped entirely.

---

## Summary

| | PostgreSQL (OLTP) | BigQuery (OLAP) |
|--|-------------------|-----------------|
| Index type | B-Tree, Hash, GIN | Partitioning + Clustering |
| Row skipping | Index lookup | Partition pruning |
| Column skipping | No | Yes (columnar) |
| Manual setup | `CREATE INDEX` | `PARTITION BY` / `CLUSTER BY` |
| Tradeoff | Faster reads, slower writes | No write penalty, scales to PBs |
