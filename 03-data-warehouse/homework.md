# Data Warehouse Homework — BigQuery

## Q1. Count of records for 2024 Yellow Taxi Data

**Answer: 20,332,093**

---

## Q2. Estimated bytes — External Table vs Materialized Table

Query: `SELECT COUNT(DISTINCT PULocationID)`

**Answer: 0 MB for External Table and 155.12 MB for Materialized Table**

| | External Table | Materialized Table |
|--|---------------|-------------------|
| Bytes processed | 0 MB | 155.12 MB |
| Duration | 964 ms | - |

External table returns 0 MB because BQ does not scan GCS data for metadata-resolvable queries.

---

## Q3. Why are estimated bytes different when querying one vs two columns?

Query 1: `SELECT PULocationID`
Query 2: `SELECT PULocationID, DOLocationID`

**Answer: BigQuery is a columnar database — it only scans the specific columns requested. Querying two columns reads more data than one.**

---

## Q4. Records with fare_amount = 0

**Answer: 8,333**

---

## Q5. Non-partitioned vs Partitioned Table bytes

Query: `SELECT DISTINCT VendorID WHERE tpep_dropoff_datetime BETWEEN 2024-03-01 AND 2024-03-15`

**Answer: 310.24 MB for non-partitioned and 26.84 MB for partitioned table**

Partitioned table scans only the relevant date partitions — significantly less data.

---

## Q6. Where is data stored in External Table?

**Answer: GCP Bucket (GCS)**

External tables store no data in BigQuery — they read directly from GCS at query time.

---

## Q7. Is it best practice to always cluster data in BigQuery?

**Answer: False**

Clustering is not always beneficial:
- Small tables (< 1 GB) — overhead outweighs benefit
- Tables not frequently filtered on cluster columns — no gain
- Use clustering only when queries regularly filter on those columns

---

## Q8. SELECT COUNT(*) — How many bytes estimated?

**Answer: 0 MB**

BigQuery stores table metadata (row count) separately. `COUNT(*)` reads from metadata, not the actual data — same as `len(data)` in Python reading the list length without iterating values.
