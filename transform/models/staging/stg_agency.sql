-- Hier beginnt die Einschränkung auf eine Agentur. Alle weiteren Staging-Modelle filtern über
-- dieses Modell, so tragen sie nur noch Daten der Verkehrsbetriebe Luzern und bleiben klein.

SELECT
    agency_id,
    agency_name,
    _PARTITIONDATE AS feed_version
FROM {{ source('raw', 'agency') }}
WHERE _PARTITIONDATE = {{ latest_version() }}
    -- LOWER, damit das Muster nicht an Gross- und Kleinschreibung im Feed hängt.
    AND LOWER(agency_name) LIKE '{{ var("agency_pattern") }}'
