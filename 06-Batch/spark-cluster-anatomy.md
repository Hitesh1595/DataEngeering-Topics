# Anatomy of a Spark Cluster

## Components

```
                        ┌─────────────────────┐
                        │   Driver Program     │
                        │  (SparkContext/      │
                        │   SparkSession)      │
                        │  - builds DAG        │
                        │  - schedules tasks   │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Cluster Manager    │
                        │ (YARN/K8s/Standalone/│
                        │       Mesos)         │
                        │  - allocates         │
                        │    resources         │
                        └──────────┬───────────┘
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
          ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
          │  Worker Node │   │  Worker Node │   │  Worker Node │
          │ ┌──────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │
          │ │ Executor │ │   │ │ Executor │ │   │ │ Executor │ │
          │ │ - tasks  │ │   │ │ - tasks  │ │   │ │ - tasks  │ │
          │ │ - cache  │ │   │ │ - cache  │ │   │ │ - cache  │ │
          │ └──────────┘ │   │ └──────────┘ │   │ └──────────┘ │
          └──────────────┘   └──────────────┘   └──────────────┘
```

## 1. Driver
- Runs the `main()` function, creates `SparkSession`/`SparkContext`.
- Converts user code (transformations) into a **logical plan**, then Catalyst optimizes into a **physical plan** (DAG).
- Splits DAG into **jobs → stages → tasks**, schedules tasks onto executors.
- Collects results back (for actions like `collect()`), tracks task status, handles failures/retries.
- Single point — if driver dies, whole application dies.

## 2. Cluster Manager
Allocates resources (CPU/memory) across the cluster for the application. Spark supports:
- **Standalone** — Spark's own simple built-in manager.
- **YARN** — Hadoop ecosystem, most common in on-prem/EMR setups.
- **Kubernetes** — containerized deployments, increasingly common.
- **Mesos** — older, less common now.

Driver asks cluster manager for executors; cluster manager launches them on worker nodes.

## 3. Worker Nodes
Physical/virtual machines in the cluster that run executor processes.

## 4. Executors
- JVM processes launched on worker nodes, one or more per node.
- Run **tasks** assigned by the driver, in parallel threads.
- Hold data in memory/disk (**cache/persist**, shuffle data) for the lifetime of the application.
- Report task status + results back to driver.
- Fixed for the duration of the app (unless dynamic allocation enabled).

## Job → Stage → Task Breakdown
- **Job**: triggered by an action (`count`, `collect`, `write`).
- **Stage**: job splits into stages at **shuffle boundaries** (wide transformations like `groupBy`, `join`).
- **Task**: stage splits into tasks — one task per partition, task = smallest unit of work, runs on one executor core.

```
Action (e.g. .write.parquet())
   → Job
      → Stage 1 (narrow transforms, no shuffle)
         → Task 1, Task 2, ... (one per partition)
      → [SHUFFLE]
      → Stage 2 (after groupBy/join)
         → Task 1, Task 2, ...
```

## Execution Modes
- **Client mode**: driver runs on the machine that launched the job (e.g. your laptop/notebook) — driver outside cluster.
- **Cluster mode**: driver runs inside the cluster itself (one of the worker nodes) — used for production jobs, more fault-tolerant.

## Spark Submit Flow — Simple Walkthrough

```
You (laptop)              Cluster                                Data Lake (S3/GCS)
┌──────────┐  spark-submit  ┌────────┐   assigns tasks   ┌───────────┐
│  Driver   │──────────────▶│ Master │──────────────────▶│ Executors │
│ (10MB job)│                │ :4040  │                   │  (workers)│
└──────────┘                └────────┘                   └─────┬─────┘
                                  │  one executor dies,          │
                                  │  master reassigns its work   │ reads partitions
                                  │  to a healthy one             │ (P1, P2, ... 100MB each)
                                  ▼                               ▼
                             (retry task)                  DataFrame on S3/GCS
```

1. You write a small Spark job (driver code, here ~10MB) on your laptop and run `spark-submit`.
2. Driver connects to the **Master** on the cluster — Master runs its UI on port **4040** (Spark UI).
3. Master hands out work to **Executors** — the actual worker processes that do the processing.
4. One executor crashes/fails (red ❌ in diagram) — Master notices, **reassigns that executor's tasks** to a different, healthy executor (red arrow curving to next box). This is Spark's fault tolerance — no manual intervention needed, job just retries on another executor.
5. Surviving executors each **pull their assigned partition** of data straight from the data lake (S3/GCS) — e.g. partition P1, P2, each ~100MB. Each executor reads only its own slice, in parallel — not the whole file.
6. Executors process their partition independently, send results/status back to Master → Driver.

**Key idea:** driver code is tiny and just coordinates; the heavy lifting (reading 100MB+ partitions, computing) happens on executors, in parallel, directly against the data lake. Losing one executor doesn't fail the job — its work just gets redone elsewhere.

## Interview Q&A

**Q: Driver vs Executor?**
A: Driver — coordinates, builds plan, schedules; runs once per application. Executor — does actual data processing (runs tasks), one or more per worker node, many per application.

**Q: What happens if an executor fails mid-job?**
A: Driver detects failure, reschedules its tasks on another executor. Lost data recomputed via RDD lineage (no data loss, just recompute cost).

**Q: What happens if the driver fails?**
A: Whole application fails — driver is single point of failure (in client mode especially). Cluster mode + checkpointing used for resilience in production.

**Q: What's a Spark "application"?**
A: One run of your driver program + all its executors for its full lifetime — can contain multiple jobs (one per action).

**Q: Client mode vs cluster mode — when use which?**
A: Client mode for interactive work (notebooks, debugging) — driver on your machine, see logs locally. Cluster mode for production — driver runs inside cluster, survives client disconnect, standard for scheduled/long-running jobs.

**Q: How many executors/cores should a job use?**
A: Depends on data size, cluster resources, partition count. Rule of thumb: enough partitions to keep all executor cores busy (partitions ≈ 2–4x total cores), avoid too many tiny partitions (task scheduling overhead) or too few large ones (skew, underutilization).
