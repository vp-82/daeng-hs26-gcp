SELECT
    route_id,
    agency_id,
    route_short_name,
    route_desc,
    -- CAST statt SAFE_CAST: steht im Feed einmal etwas anderes als eine Zahl, soll der Lauf
    -- abbrechen, statt still NULL zu schreiben.
    CAST(route_type AS INT64) AS route_type,
    _PARTITIONDATE AS feed_version
FROM {{ source('raw', 'routes') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    AND agency_id IN (SELECT agency_id FROM {{ ref('stg_agency') }})
