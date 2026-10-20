SELECT
    service_id,
    -- GTFS schreibt 1 und 0. CAST('1' AS BOOL) kennt BigQuery nicht, darum der Vergleich.
    monday = '1' AS monday,
    tuesday = '1' AS tuesday,
    wednesday = '1' AS wednesday,
    thursday = '1' AS thursday,
    friday = '1' AS friday,
    saturday = '1' AS saturday,
    sunday = '1' AS sunday,
    PARSE_DATE('%Y%m%d', start_date) AS start_date,
    PARSE_DATE('%Y%m%d', end_date) AS end_date,
    _PARTITIONDATE AS feed_version
FROM {{ source('raw', 'calendar') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    -- Der Kalender gilt für die ganze Schweiz; wir behalten nur Dienste, die Luzerner Fahrten haben.
    AND service_id IN (SELECT service_id FROM {{ ref('stg_trips') }})
