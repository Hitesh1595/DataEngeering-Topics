# Docker Setup

## How it works

```
[ your machine ]
      |
      |-- pipeline_default (Docker network)
            |
            |-- pgdatabase (Postgres container)   ← hostname on the network
            |-- taxi_ingest (ingest container)     ← connects to pgdatabase
```

Containers on the same Docker network talk to each other using the **service name as hostname**.
The network name `pipeline_default` is auto-created by compose using the project `name: pipeline`.

---

## Run Postgres standalone (without compose)

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

---

## Run ingest script locally (Postgres must be running)

```bash
uv run python ingest_data.py \
    --pg-host localhost \
    --pg-port 5432 \
    --pg-user root \
    --pg-pass root \
    --pg-db ny_taxi \
    --table yellow_taxi_data
```

---

## Run ingest container (with compose network)

Start Postgres via compose first:
```bash
docker-compose up -d
```

Then run the ingest container on the same network.
`--pg-host=pgdatabase` works because `pgdatabase` is the service name in docker-compose.yml,
which becomes its DNS hostname on the `pipeline_default` network.

```bash
docker run -it --rm \
    --network=pipeline_default \
    taxi_ingest:v001 \
    --pg-host=pgdatabase
```

> **Why not localhost?**
> Inside a container, `localhost` means the container itself — not the Postgres container.
> Use the service name `pgdatabase` to reach across the network.
