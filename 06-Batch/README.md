# Batch vs Streaming + Spark — Interview Notes

## 1. Batch Processing
**Definition:** process data in fixed chunks at scheduled intervals (hourly/daily). Reads a bounded dataset, computes, writes output, stops.

```python
df = spark.read.parquet("s3://data/2026-09-27/")
result = df.groupBy("user_id").count()
result.write.parquet("s3://output/")
```

**Pros:** simple to write/test/debug (deterministic, bounded input), easy reprocess/backfill, lower infra cost (runs on schedule), mature tooling for retries/failures.
**Cons:** high latency, not real-time, resource spikes during runs.

## 2. Streaming Processing
**Definition:** process data continuously as it arrives — unbounded input (Spark Structured Streaming, Kafka, Flink).

```python
df = spark.readStream.format("kafka").option("subscribe", "events").load()
query = df.groupBy("user_id").count().writeStream.outputMode("update").start()
```

**Pros:** low latency/near real-time, powers dashboards/alerts/fraud detection, natural fit for unbounded data.
**Cons:** complex (state management, watermarking, late data), harder exactly-once guarantees, higher infra cost (always running), harder to reprocess history.

## 3. Batch vs Streaming — Quick Comparison

| | Batch | Streaming |
|---|---|---|
| Data | Bounded, finite | Unbounded, continuous |
| Latency | Minutes–hours | Milliseconds–seconds |
| Cost | Runs on schedule (cheaper) | Always-on (costlier) |
| Complexity | Lower | Higher (state, watermarks, late data) |
| Use case | Reports, ETL, backfills | Fraud detection, alerts, live dashboards |
| Fault tolerance | Simple retry of whole job | Checkpointing, exactly-once semantics |

**Interview one-liner:** "Batch trades latency for simplicity and cost; streaming trades cost and complexity for freshness."

## 4. Apache Spark — What It Is
- Multi-language engine for large-scale data processing (data engineering, data science, ML) — single machine or cluster.
- **Engine**: pulls data from a DB/data lake into its own executors, processes there, writes results back.
- **Distributed**: cluster of many machines pulling/processing/saving in parallel.
- **Multi-language**: native Scala, wrappers for Java, R, Python (**PySpark** — most popular). Some teams rewrite hot paths in Scala for performance.
- Mainly **batch**; also does streaming (as sequence of micro-batches — Structured Streaming).

## 5. When to Use Spark vs SQL Engines
Typical case: data in a data lake (Parquet on S3/GCS). SQL on a warehouse (BigQuery) is easy; SQL directly on lake files is harder — though Hive, Presto, Athena, BigQuery external tables make it possible.

**Rule of thumb:**
> Job expressible as SQL → use Presto/Athena/BigQuery.
> Not expressible as SQL → use Spark.

Use Spark for: complex logic that doesn't fit SQL, unmanageable queries, modular code, unit testing, machine learning (training + inference).

## 6. Typical Workflow
1. Raw data lands in data lake.
2. Transformations/aggregations/joins via SQL (Athena/Presto).
3. Complex step needs Spark — e.g., Python job training ML model.
4. Another Spark job applies trained model (inference), writes results back to lake.
5. Results flow onward to data warehouse or other destinations.

Most pre-processing happens in SQL stage; Spark handles what SQL can't.

## 7. Spark Architecture (common interview topic)
- **Driver**: runs the main program, builds the DAG of transformations, schedules tasks.
- **Cluster Manager**: allocates resources (YARN, Kubernetes, Spark Standalone, Mesos).
- **Executors**: worker processes on cluster nodes; run tasks, store data in memory/disk, report back to driver.
- **Job → Stages → Tasks**: a job splits into stages at shuffle boundaries; each stage splits into tasks (one per partition).

## 8. Core Concepts
- **RDD (Resilient Distributed Dataset):** low-level, immutable, distributed collection; fault-tolerant via lineage (DAG of transformations, recompute lost partitions instead of replicating data).
- **DataFrame:** RDD + schema, higher-level API, optimized via **Catalyst optimizer** and **Tungsten execution engine**. Preferred over RDDs in practice.
- **Lazy evaluation:** transformations (`map`, `filter`, `select`, `groupBy`) build a DAG but don't execute until an **action** (`collect`, `count`, `write`) triggers it. Lets Spark optimize the whole plan before running.
- **Transformations vs Actions:**
  - Transformations (lazy): `map`, `filter`, `select`, `join`, `groupBy`
  - Actions (trigger execution): `count`, `collect`, `show`, `write`, `take`
- **Partitions:** unit of parallelism; data split across partitions, each processed by one task. Wrong partition count → skew/slow jobs.
- **Shuffle:** redistributing data across partitions (e.g., for `groupBy`, `join`) — expensive, network + disk I/O; a common perf-tuning target.
- **Wide vs Narrow transformations:**
  - Narrow: each input partition maps to one output partition, no shuffle (`map`, `filter`).
  - Wide: requires shuffle across partitions (`groupBy`, `join`, `distinct`).

## 9. Common Interview Q&A
**Q: Difference between RDD and DataFrame?**
A: RDD is low-level, no schema, no query optimizer, more control. DataFrame has schema, benefits from Catalyst/Tungsten optimization, easier/faster for most use cases.

**Q: Why is Spark faster than Hadoop MapReduce?**
A: In-memory computation (avoids writing intermediate results to disk each stage), DAG-based execution plan, lazy evaluation + optimizer.

**Q: What causes data skew and how do you fix it?**
A: Uneven key distribution → some partitions/tasks do much more work. Fix: salting keys, repartitioning, broadcast join for small tables.

**Q: What's a broadcast join?**
A: Small table sent (broadcast) to all executors, avoiding shuffle of the large table — used when one side of a join is small enough to fit in memory.

**Q: How does Spark achieve fault tolerance?**
A: RDD lineage — DAG of transformations lets Spark recompute lost partitions from source instead of needing replication.

**Q: What is a shuffle and why avoid it?**
A: Repartitioning data across the cluster (network + disk heavy) required for wide transformations like `groupBy`/`join`. Minimize via broadcast joins, pre-partitioning, fewer wide transformations.

**Q: Batch vs streaming — when would you pick each?**
A: Batch for scheduled reports/ETL/backfills where minutes-hours latency is fine and cost/simplicity matter. Streaming for fraud detection, real-time alerts, live dashboards where seconds-level latency is required.

**Q: How does Spark Structured Streaming model streaming?**
A: As a sequence of small/micro-batches on an unbounded table — same DataFrame API as batch, so code is largely reusable.
