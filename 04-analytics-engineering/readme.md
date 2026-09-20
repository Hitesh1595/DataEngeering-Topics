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
    │   ├── staging/            # 1:1 with source tables, light cleanup (renames, types, filters)
    │   │   └── source.yml      # declares raw source tables dbt reads from, enables source() refs + freshness checks
    │   ├── intermediate/       # joins/aggregates staging models, not exposed to end users
    │   └── marts/              # final business-facing tables, one per domain/use case
    ├── seeds/                  # static CSV files loaded into the warehouse via `dbt seed`
    ├── snapshots/              # SCD Type 2 snapshots for tracking slowly changing data
    ├── tests/                  # custom data tests (assertions on model output)
    ├── macros/                 # reusable Jinja macros/functions used across models
    ├── analyses/               # ad-hoc analysis SQL, compiled but never materialized
    └── logs/                   # dbt run/debug logs
```

### source.yml

Declares dbt's `sources` — pointers to raw tables already loaded into the warehouse (not created by dbt itself). Lives under `models/staging/` since staging models consume it.

- Lets models reference raw tables via `{{ source('source_name', 'table_name') }}` instead of hardcoding schema/table names — one place to update if raw location changes.
- Supports source freshness checks (`dbt source freshness`) to flag stale upstream data.
- Documents raw tables (descriptions, columns, tests) so they show up in dbt docs alongside models.
- Builds the lineage graph back to raw data, so `dbt docs generate` and `dbt run --select +model` know the true starting point.

**Example — `source.yml`:**

```yaml
version: 2

sources:
  - name: raw_data          # name used in source() calls
    database: my_db
    schema: prod             # actual schema in the warehouse
    tables:
      - name: green_tripdata # actual table name in the warehouse
        description: "Green taxi trip data"
```

**Used in a staging model (`stg_green_tripdata.sql`):**

```sql
select *
from {{ source('raw_data', 'green_tripdata') }}
where vendorid is not null
```




### fact vs dimension

Dimensional modeling split for marts models.

- **Fact** (`fct_`): measurable events/transactions — one row per event, mostly numeric measures + foreign keys to dimensions. Grows fast, no descriptive detail. Example: `fct_trips` (trip distance, fare, pickup/dropoff datetime, vendor_id, payment_type_id).
- **Dimension** (`dim_`): descriptive, mostly-static context that facts join to. Slow-changing, human-readable attributes. Example: `dim_vendors` (vendor_id, vendor_name), `dim_payment_types` (payment_type_id, payment_type_name).

### ref() vs source()

Both are Jinja functions that resolve to a table/view name at compile time — never hardcode table names in model SQL.

- **`source()`** — points to a raw table declared in `source.yml`, i.e. data dbt did not build. Only used in staging models (the entry point into dbt).
- **`ref()`** — points to another dbt model (built by `dbt run`). Used everywhere downstream of staging (intermediate, marts).

```sql
-- staging model: reads raw data
select * from {{ source('raw_data', 'green_tripdata') }}

-- mart model: reads another dbt model
select * from {{ ref('stg_green_tripdata') }}
```

`ref()` is also what builds the DAG — dbt parses every `ref()`/`source()` call to know run order and draw lineage.
