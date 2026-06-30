# Data Flow — Workflow Orchestration (Kestra)

## Pipeline 1 — PostgreSQL (flows 04 & 05)

```
GitHub Releases (.csv.gz)
        │  wget + gunzip
        ▼
Kestra Internal Storage (.csv)
        │  TRUNCATE staging
        │  CopyIn (bulk load)
        ▼
Staging Table
        │  UPDATE: add MD5 unique_row_id + filename
        ▼
Staging Table (enriched)
        │  MERGE ON unique_row_id (INSERT WHEN NOT MATCHED)
        ▼
Main Table (PostgreSQL)
        │  purge_files
        ▼
Kestra Storage Cleaned
```

---

## Pipeline 2 — GCS + BigQuery (flows 08 & 09)

```
GitHub Releases (.csv.gz)
        │  wget + gunzip
        ▼
Kestra Internal Storage (.csv)
        │  GCS Upload
        ▼
Google Cloud Storage (gs://bucket/file.csv)
        │  CREATE EXTERNAL TABLE (reads GCS directly)
        ▼
BigQuery External Table (_ext)
        │  CREATE TABLE AS SELECT + MD5 unique_row_id
        ▼
BigQuery Temp Table (_YYYY_MM)
        │  MERGE ON unique_row_id (INSERT WHEN NOT MATCHED)
        ▼
BigQuery Main Table (partitioned by date)
        │  purge_files
        ▼
Kestra Storage Cleaned
```

---

## Scheduling (flows 05 & 09)

Both pipelines run on the 1st of every month via cron triggers.  
Supports backfill from the Kestra UI using `trigger.date` to derive the file name.
