# Partitioning in BigQuery

## What is Partitioning

Splitting a table into segments based on a column value so that queries only scan the relevant segment instead of the full table.

```
yellow_tripdata (partitioned by DATE(tpep_pickup_datetime))

Partition 2019-01-01  │  rows for Jan 1
Partition 2019-01-02  │  rows for Jan 2
Partition 2019-01-03  │  rows for Jan 3
...
```

A query filtering `WHERE DATE(tpep_pickup_datetime) = '2019-01-01'` scans **only that partition**, not the entire table.

---

## Types of Partitioning in BigQuery

### 1. Time-based (most common)
```sql
CREATE TABLE yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime);
```
Partitions by day automatically. Can also use `MONTH` or `YEAR`:
```sql
PARTITION BY DATE_TRUNC(tpep_pickup_datetime, MONTH)
```

### 2. Integer Range
```sql
PARTITION BY RANGE_BUCKET(vendor_id, GENERATE_ARRAY(0, 100, 10))
```

### 3. Ingestion Time
```sql
PARTITION BY _PARTITIONDATE
```
Partitions by when the row was inserted into BQ.

---

## Cost & Performance Impact

Without partitioning — query scans entire table:
```
Query: WHERE DATE(pickup) = '2019-01-01'
Scans: 10 GB (all years, all months)
Cost:  $0.05
```

With partitioning:
```
Query: WHERE DATE(pickup) = '2019-01-01'
Scans: 30 MB (only Jan 1 partition)
Cost:  ~$0.00015
```

BQ charges $5 per TB scanned — partitioning directly reduces cost.

---

## In This Course

```sql
CREATE TABLE IF NOT EXISTS yellow_tripdata
(...)
PARTITION BY DATE(tpep_pickup_datetime);
```

Each day of taxi trips is a separate partition. Loading a new month adds new partitions without touching existing ones.

---

## Key Points

- Max **4000 partitions** per table in BigQuery
- Always filter on the partition column in WHERE clause to benefit
- BQ shows bytes to be scanned in the query editor before running
- Works best when queries regularly filter by the partition column
