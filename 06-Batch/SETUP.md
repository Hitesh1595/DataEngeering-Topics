# Local Dev Setup — Docker + Jupyter (PySpark)

Runs PySpark inside a Jupyter Notebook/Lab container. No local Spark/Java install needed.

## Files
- `Dockerfile` — builds image from `jupyter/pyspark-notebook` base + installs `requirements.txt`
- `docker-compose.yml` — runs container, mounts whole `work/` dir to `/home/jovyan/work` (everything saved anywhere in Jupyter syncs to host automatically), exposes Jupyter (8888) and Spark UI (4040)
- `requirements.txt` — Python deps (pyspark, pandas, pyarrow)
- `work/notebooks/` — put your `.ipynb` files here
- `work/data/` — put input files here (parquet/csv), read from `/home/jovyan/work/data` inside container

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
- Whole `work/` dir is mounted, not just subfolders — any file saved anywhere under `/home/jovyan/work` inside the notebook (downloads, new folders, scratch files) shows up on host automatically. No need to save into a specific subfolder.
- To use a different Spark version, change the base image tag in `Dockerfile` (e.g. `jupyter/pyspark-notebook:spark-3.4.1`).
- Large data files (csv/parquet) are gitignored under `work/data/` — don't commit datasets.
