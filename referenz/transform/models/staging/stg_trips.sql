SELECT
    trip_id,
    route_id,
    -- service_id verbindet die Fahrt mit dem Kalender: mehrere Fahrten teilen sich dieselben Fahrtage.
    service_id,
    trip_headsign,
    CAST(direction_id AS INT64) AS direction_id,
    _PARTITIONDATE AS feed_version
FROM {{ source('raw', 'trips') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    AND route_id IN (SELECT route_id FROM {{ ref('stg_routes') }})
