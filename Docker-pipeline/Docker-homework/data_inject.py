import pandas as pd
from sqlalchemy import create_engine
import click

pg_user = "root"
pg_pass = "root"
pg_host = "localhost"
pg_port = 5432
pg_db = "ny_taxi"

green_trip_data_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-11.parquet"
taxi_zone_lookup_url = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv"

green_data = pd.read_parquet(green_trip_data_url)
taxi_zone = pd.read_csv(taxi_zone_lookup_url)

print("shape", green_data.shape)

engine = create_engine(f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")

taxi_zone.head(0).to_sql(name="taxi_zone", con=engine, if_exists="replace")
taxi_zone.to_sql(name="taxi_zone", con=engine, if_exists="append")

green_data.head(0).to_sql(name="green_trip", con=engine, if_exists="replace")
green_data.to_sql(name="green_trip", con=engine, if_exists="append")

click.echo(f"Done — data loaded into '{pg_db}'.")





