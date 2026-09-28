# Local Dev Setup — Docker + Jupyter (PySpark)

Runs PySpark inside a Jupyter Notebook/Lab container. No local Spark/Java install needed.

## Files
- `Dockerfile` — builds image from `jupyter/pyspark-notebook` base + installs `requirements.txt`
- `docker-compose.yml` — runs container, mounts `notebooks/` and `data/`, exposes Jupyter (8888) and Spark UI (4040)
- `requirements.txt` — Python deps (pyspark, pandas, pyarrow)
- `notebooks/` — put your `.ipynb` files here (mounted, persists on host)
- `data/` — put input files here (parquet/csv), read from `/home/jovyan/work/data` inside container

## Usage

Build and start:
```bash
docker compose up --build
```

Open Jupyter Lab in browser:
```
http://localhost:8888
```
(no token — set to empty in compose for local dev convenience)

Stop:
```bash
docker compose down
```

Rebuild after changing `requirements.txt`:
```bash
docker compose up --build
```

## Verify PySpark works

In a notebook cell:
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("test").getOrCreate()
df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "val"])
df.show()
```

While a job runs, Spark UI available at:
```
http://localhost:4040
```

## Notes
- Data placed in `./data` on host shows up at `/home/jovyan/work/data` in container — use that path in `spark.read.parquet(...)` etc.
- Notebooks saved in `./notebooks` persist across container restarts/rebuilds.
- To use a different Spark version, change the base image tag in `Dockerfile` (e.g. `jupyter/pyspark-notebook:spark-3.4.1`).
