# BigQuery Best Practices

## 1. Always Partition Large Tables

```sql
-- always partition by the column most used in WHERE filters
CREATE TABLE yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime);
```

- Use `DATE` partition for time-series data
- Filter on partition column in every query — otherwise BQ scans full table
- Max 4000 partitions per table

---

## 2. Cluster After Partitioning

```sql
CREATE TABLE yellow_tripdata
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID, PULocationID;
```

- Add clustering on columns frequently used in WHERE, JOIN, GROUP BY
- Put highest cardinality / most filtered column first
- Free — BQ manages it automatically

---

## 3. Never Use SELECT *

```sql
-- bad: scans all columns (you pay for all data)
SELECT * FROM yellow_tripdata;

-- good: only scan what you need
SELECT VendorID, fare_amount, tpep_pickup_datetime
FROM yellow_tripdata;
```

BQ charges per bytes scanned — unused columns cost money.

---

## 4. Always Filter on Partition Column

```sql
-- bad: scans entire table across all partitions
SELECT COUNT(*) FROM yellow_tripdata
WHERE VendorID = '1';

-- good: partition pruning kicks in
SELECT COUNT(*) FROM yellow_tripdata
WHERE DATE(tpep_pickup_datetime) = '2019-01-01'
  AND VendorID = '1';
```

---

## 5. Avoid Updates — Use MERGE or Append

```sql
-- bad: rewrites entire column file, expensive
UPDATE yellow_tripdata SET fare_amount = 10 WHERE trip_id = 123;

-- good: use MERGE for corrections
MERGE INTO yellow_tripdata T
USING corrections S
ON T.unique_row_id = S.unique_row_id
WHEN MATCHED THEN UPDATE SET fare_amount = S.corrected_fare
WHEN NOT MATCHED THEN INSERT ...;
```

Design pipelines to be **append-only** where possible. Save MERGE for corrections.

---

## 6. Use External Tables for Raw Data

```sql
-- point BQ at GCS file without copying data
CREATE OR REPLACE EXTERNAL TABLE dataset.yellow_ext
OPTIONS (
    format = 'CSV',
    uris = ['gs://bucket/yellow_tripdata_2019_01.csv'],
    skip_leading_rows = 1
);
```

- No storage cost for external tables
- Good for one-time queries or schema validation before loading
- Cannot add computed columns — materialize into native table when needed

---

## 7. Use ELT Not ETL

```
ETL (old way):  transform on ETL server → load clean data → BQ
ELT (BQ way):   load raw → GCS → BQ → transform inside BQ with SQL/dbt
```

- Load raw data first — always preserve source of truth in GCS
- Transform inside BQ — cheaper, faster, more flexible
- Use dbt for SQL-based transformations on top of BQ

---

## 8. Use GCS as Data Lake, BQ as Warehouse

```
GCS  → raw files, any format, cheap storage, never delete
BQ   → structured tables, SQL queries, analytics
```

- Never skip GCS and load directly into BQ — you lose the raw backup
- If BQ table gets corrupted, raw GCS files let you rebuild from scratch
- External tables bridge the two — BQ queries GCS without copying

---

## 9. Deduplicate with MD5 Hash

```sql
-- generate unique row id from business keys
MD5(CONCAT(
    COALESCE(CAST(VendorID AS STRING), ""),
    COALESCE(CAST(tpep_pickup_datetime AS STRING), ""),
    COALESCE(CAST(PULocationID AS STRING), "")
)) AS unique_row_id
```

- Never rely on auto-increment IDs across systems
- MD5 of key business fields = deterministic dedup key
- Same row reprocessed → same hash → MERGE skips it

---

## 10. Production DB vs BigQuery — Keep Both

```
Production DB               BigQuery
─────────────               ────────
App writes here             Analysts query here
Current state only          Full history forever
Row-level operations        Aggregations, reports
Low latency (ms)            Higher latency (seconds)
Small retention window      Years of data
```

- Never delete from production DB just because data is in BQ
- ETL extracts incrementally — only new/changed rows each run
- Analysts, dashboards, ML models always query BQ — never production DB

---

## 11. Incremental Loads Over Full Loads

```sql
-- bad: extract entire table every day
SELECT * FROM orders;

-- good: extract only new rows
SELECT * FROM orders
WHERE updated_at > '{{ last_run_timestamp }}'
  AND updated_at <= '{{ current_run_timestamp }}';
```

- Full loads waste time, money, and bandwidth on unchanged data
- Use watermark column (`created_at`, `updated_at`) for incremental
- For real-time use CDC (Change Data Capture) tools like Debezium + Kafka

---

## 12. Cost Awareness

| Action | Cost |
|--------|------|
| Query without partition filter | High — scans full table |
| Query with partition filter | Low — scans one partition |
| `SELECT *` | High — reads all columns |
| `SELECT col1, col2` | Low — reads only those columns |
| `UPDATE` / `DELETE` | High — rewrites column files |
| `INSERT` / `MERGE` | Lower — append friendly |
| External table storage | Free |
| Native table storage | ~$0.02/GB/month |
| Query processing | $5/TB scanned |

Always check **bytes to be processed** in BQ UI before running heavy queries.
