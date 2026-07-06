select count(*) from yellow_taxi_data ytd ;

SELECT * FROM information_schema.tables
WHERE table_schema = 'public';

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'yellow_taxi_data';


select * from yellow_taxi_data ytd;

select * from yellow_taxi_data ytd limit 10;

SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    "PULocationID",
    "DOLocationID"
FROM
    yellow_taxi_data
WHERE
    "PULocationID" IS NULL
    OR "DOLocationID" IS NULL
LIMIT 100;


select CAST(tpep_dropoff_datetime as DATE) as day,
	"DOLocationID",
    count(*) as count,
	MAX(total_amount) AS total_amount,
    MAX(passenger_count) AS passenger_count
from yellow_taxi_data ytd 
group by CAST(tpep_dropoff_datetime as DATE),"DOLocationID"
order by count desc
limit 100