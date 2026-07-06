# OLAP vs OLTP

## OLTP (Online Transaction Processing)

Designed for day-to-day transactional operations — insert, update, delete individual rows fast.

| Property | Detail |
|----------|--------|
| Purpose | Record business transactions |
| Operations | INSERT, UPDATE, DELETE |
| Query type | Simple, row-level |
| Data size | GBs |
| Users | Application backend, end users |
| Examples | PostgreSQL, MySQL, Oracle |

**Example query:**
```sql
SELECT * FROM orders WHERE order_id = 12345;
```

---

## OLAP (Online Analytical Processing)

Designed for analytical queries — aggregate, scan, and analyze large volumes of historical data.

| Property | Detail |
|----------|--------|
| Purpose | Business intelligence, reporting |
| Operations | SELECT with aggregations |
| Query type | Complex, multi-table, full scans |
| Data size | TBs to PBs |
| Users | Analysts, data scientists |
| Examples | BigQuery, Snowflake, Redshift, ClickHouse |

**Example query:**
```sql
SELECT DATE(pickup_datetime), COUNT(*), AVG(fare_amount)
FROM yellow_tripdata
WHERE YEAR(pickup_datetime) = 2019
GROUP BY 1 ORDER BY 1;
```

---

## Key Differences

| | OLTP | OLAP |
|--|------|------|
| Optimized for | Write speed | Read/scan speed |
| Data model | Normalized (3NF) | Denormalized (star/snowflake schema) |
| Indexes | Many, on primary/foreign keys | Few, on partition/cluster keys |
| Row vs Column storage | Row-oriented | Column-oriented |
| Latency | Milliseconds | Seconds to minutes |
| Backup concern | High (live transactions) | Lower (can rebuild from source) |

---

## In This Course

| System | Type |
|--------|------|
| PostgreSQL (Docker) | OLTP |
| BigQuery | OLAP |

Data flows from OLTP (source systems) → ingestion pipeline → OLAP (BigQuery) for analysis.
