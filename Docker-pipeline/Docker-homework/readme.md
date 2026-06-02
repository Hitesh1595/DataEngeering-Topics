# Docker Homework

## Question 1 — pip version inside python:3.13 container

```bash
docker run -it --rm python:3.13 bash
pip --version
```

**Answer:** `pip 26.0.1`

---

## Question 2 — Docker networking and docker-compose

**Answer:** `db:5433`

---

## Question 3 — Trips with distance ≤ 1 mile in November 2025

```sql
SELECT COUNT(*)
FROM green_trip gt
WHERE gt.lpep_pickup_datetime >= '2025-11-01 00:00:00'
  AND gt.lpep_pickup_datetime < '2025-12-01 00:00:00'
  AND gt.trip_distance <= 1;
```

**Answer:** `8007`

---

## Question 4 — Pickup day with the longest trip distance (< 100 miles)

```sql
SELECT CAST(gt.lpep_pickup_datetime AS DATE), MAX(trip_distance) AS max_trip
FROM green_trip gt
WHERE gt.trip_distance < 100
GROUP BY CAST(gt.lpep_pickup_datetime AS DATE)
ORDER BY max_trip DESC
LIMIT 1;
```

**Answer:** `2025-11-14`

---

## Question 5 — Pickup zone with the largest total amount on November 18th, 2025

```sql
SELECT
    tz."Zone",
    SUM(gt.total_amount) AS total_amount_sum
FROM green_trip gt
INNER JOIN taxi_zone tz
    ON gt."PULocationID" = tz."LocationID"
WHERE gt.lpep_pickup_datetime >= '2025-11-18'::TIMESTAMP
  AND gt.lpep_pickup_datetime < '2025-11-19'::TIMESTAMP
GROUP BY tz."Zone"
ORDER BY total_amount_sum DESC
LIMIT 1;
```

**Answer:** `East Harlem North`

---

## Question 6 — Drop-off zone with the largest tip from "East Harlem North" in November 2025

```sql
SELECT
    tz_do."Zone" AS dropoff_zone,
    MAX(gt.tip_amount) AS max_tip
FROM green_trip gt
INNER JOIN taxi_zone tz_pu
    ON gt."PULocationID" = tz_pu."LocationID"
INNER JOIN taxi_zone tz_do
    ON gt."DOLocationID" = tz_do."LocationID"
WHERE tz_pu."Zone" = 'East Harlem North'
  AND gt.lpep_pickup_datetime >= '2025-11-01'::TIMESTAMP
  AND gt.lpep_pickup_datetime < '2025-12-01'::TIMESTAMP
GROUP BY tz_do."Zone"
ORDER BY max_tip DESC
LIMIT 1;
```
