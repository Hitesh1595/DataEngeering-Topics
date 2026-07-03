# GCP Data Engineering Flow

## Standard GCP Pipeline Pattern

```
Raw File (CSV/JSON)
        │
        ▼
GCS (data lake / raw storage)       ← always land raw data here first
        │
        ▼
BigQuery External Table             ← query GCS directly, no ingestion cost
        │
        ▼
BigQuery Native Temp Table          ← materialize + add computed columns
        │
        ▼
BigQuery Main Table                 ← deduplicated, partitioned, production-ready
```

---

## Why This Order

**GCS first**
Raw files are always preserved. Cheap storage, acts as source of truth. If anything breaks downstream, raw data is still there to reprocess.

**External Table**
BigQuery reads directly from GCS without copying data. No storage cost, no ingestion job. Good for schema validation and lightweight queries before committing to a full load.

**Native Temp Table**
External tables are read-only — you can't add computed columns to them. Materializing into a native table allows adding `unique_row_id` (MD5 hash), `filename`, and any other enrichments. Also faster to query than external tables.

**MERGE into Main Table**
Idempotent upsert — re-running the pipeline for the same month never creates duplicates. Only rows where `unique_row_id` is not already present get inserted.

---

## Medallion Architecture

This pattern maps directly to the industry-standard **Medallion Architecture**:

| Layer | Name | In This Pipeline |
|-------|------|-----------------|
| Bronze | Raw | GCS `.csv` file |
| Silver | Cleaned / Enriched | BQ external + native temp table |
| Gold | Production-ready | BQ main table (deduplicated, partitioned) |

Same pattern used in **Databricks**, **dbt**, **Apache Iceberg**, and most modern data stacks.

---

## BigQuery Specific Concepts

### External Table
- Metadata only — no data copied into BQ storage
- Reads file from GCS at query time
- `CREATE OR REPLACE` — safe to rerun, always points to latest GCS file
- Cannot add computed columns or indexes

### Native Table (Temp)
- Full BQ storage — fast queries
- `CREATE OR REPLACE` — recreated fresh each pipeline run
- MD5 hash computed here: `MD5(CONCAT(vendor + pickup + dropoff + locations))`
- Acts as staging layer before merge

### Main Table
- `CREATE TABLE IF NOT EXISTS` — created once, accumulates all data
- `PARTITION BY DATE(tpep_pickup_datetime)` — splits data by day, queries only scan relevant partitions (cost + performance)
- Grows over time as new months are loaded via MERGE

### MERGE Statement
```sql
MERGE INTO main_table T
USING temp_table S
ON T.unique_row_id = S.unique_row_id
WHEN NOT MATCHED THEN INSERT ...
```
- No `WHEN MATCHED` clause — existing rows are never updated or deleted
- Pure append of new unique rows only

---

## Cost Considerations

| Operation | Cost |
|-----------|------|
| GCS storage | Very cheap (~$0.02/GB/month) |
| BQ external table query | Charged per bytes scanned from GCS |
| BQ native table storage | ~$0.02/GB/month |
| BQ query on partitioned table | Only scans relevant partitions — much cheaper |
| BQ MERGE | Charged per bytes processed |

Partitioning the main table by pickup date means a query filtering on one month scans only that month's data, not the entire table.

---

## Re-run Safety

Every step is idempotent — the pipeline can be re-run for the same month without side effects:

| Step | How it's safe |
|------|--------------|
| GCS Upload | Overwrites same file path |
| External Table | `CREATE OR REPLACE` |
| Temp Table | `CREATE OR REPLACE` |
| Main Table | `CREATE TABLE IF NOT EXISTS` |
| MERGE | `INSERT WHEN NOT MATCHED` only |
