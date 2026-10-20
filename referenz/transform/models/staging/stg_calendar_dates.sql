SELECT
    service_id,
    PARSE_DATE('%Y%m%d', `date`) AS `date`,
    CAST(exception_type AS INT64) AS exception_type,
    _PARTITIONDATE AS feed_version
FROM {{ source('raw', 'calendar_dates') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    -- Gut zehn Millionen Ausnahmen für die ganze Schweiz; nur die Luzerner Dienste interessieren.
    AND service_id IN (SELECT service_id FROM {{ ref('stg_trips') }})
