https://duckdb.org/docs/lts/operations_manual/duckdb_docker

docker compose up -d
docker compose exec dbt bash
docker compose exec duckdb duckdb
--run this duckdb -ui

docker run --rm -it -v "$(pwd):/workspace" -w /workspace --net host duckdb/duckdb duckdb -ui

## dbt project tree

```
dbt/
└── taxi_rides_ny/              # dbt project root
    ├── dbt_project.yml         # project config: name, profile, file paths, materialization defaults
    ├── models/                 # SQL transformation models, dbt's core building block
    ├── seeds/                  # static CSV files loaded into the warehouse via `dbt seed`
    ├── snapshots/              # SCD Type 2 snapshots for tracking slowly changing data
    ├── tests/                  # custom data tests (assertions on model output)
    ├── macros/                 # reusable Jinja macros/functions used across models
    ├── analyses/               # ad-hoc analysis SQL, compiled but never materialized
    └── logs/                   # dbt run/debug logs
```
