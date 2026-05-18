import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

# Column types for NYC TLC yellow taxi data
DTYPE = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64",
}

PARSE_DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]


@click.command()
@click.option("--pg-user", default="root", show_default=True, help="PostgreSQL user")
@click.option("--pg-pass", default="root", show_default=True, help="PostgreSQL password")
@click.option("--pg-host", default="localhost", show_default=True, help="PostgreSQL host")
@click.option("--pg-port", default=5432, show_default=True, type=int, help="PostgreSQL port")
@click.option("--pg-db", default="ny_taxi", show_default=True, help="PostgreSQL database name")
@click.option("--table", default="yellow_taxi_data", show_default=True, help="Target table name")
@click.option("--chunksize", default=100_000, show_default=True, type=int, help="Rows per insert batch")
def ingest(pg_user, pg_pass, pg_host, pg_port, pg_db, table, chunksize):
    """Ingest a CSV (or CSV.GZ) file from URL into a PostgreSQL table."""

    engine = create_engine(
        f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )
    url = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz'

    # Stream the file in chunks to avoid loading everything into memory
    df_iter = pd.read_csv(
        url,
        dtype=DTYPE,
        parse_dates=PARSE_DATES,
        iterator=True,
        chunksize=chunksize,
    )

    first_chunk = True
    for df_chunk in tqdm(df_iter, desc="Ingesting chunks"):
        if first_chunk:
            # Create (or replace) the table schema using the first chunk's columns
            df_chunk.head(0).to_sql(name=table, con=engine, if_exists="replace")
            click.echo(pd.io.sql.get_schema(df_chunk, name=table, con=engine))
            first_chunk = False

        df_chunk.to_sql(name=table, con=engine, if_exists="append")

    click.echo(f"Done — data loaded into '{pg_db}.{table}'.")


if __name__ == "__main__":
    ingest()
