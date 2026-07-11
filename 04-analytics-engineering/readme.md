https://duckdb.org/docs/lts/operations_manual/duckdb_docker

docker compose up -d
docker compose exec dbt bash
docker compose exec duckdb duckdb
--run this duckdb -ui

docker run --rm -it -v "$(pwd):/workspace" -w /workspace --net host duckdb/duckdb duckdb -ui
