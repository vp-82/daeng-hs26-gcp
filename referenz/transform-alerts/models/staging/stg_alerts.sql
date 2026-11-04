-- Die Bahnverkehrsinformationen der SBB, aufgeräumt: eine Zeile pro Meldung, Zeiten als echte
-- Zeitstempel, Text ohne HTML. Drei Dinge an der Quelle muss man dafür kennen:
-- 1. Jede Aktualisierung einer Meldung ist beim Publisher eine neue Zeile. Wir behalten pro
--    Meldung nur die neueste Fassung.
-- 2. published ist echtes UTC. startdatetime und enddatetime sind Schweizer Lokalzeit, tragen
--    aber den Offset +00:00. Wir lesen sie ohne Offset und hängen die Zeitzone Europe/Zurich an.
-- 3. description hat keine Leerzeichen zwischen den Sätzen, weil das HTML dort <br /> hatte.
--    Wir nehmen description_html und ersetzen die Tags.
--
-- Das Fenster: nur die Tage von alerts_from bis alerts_to, Standard Oktober 2026, als Literale,
-- damit BigQuery nur diese Partitionen liest. Lektion 3 rechnet auf einem festen Monat, damit
-- die Zahlen bei allen gleich sind. Im Betrieb setzt man das Fenster auf die letzten Tage:
-- dbt build --vars '{alerts_from: "2026-11-01", alerts_to: "2026-11-30"}'

WITH rows_in_window AS (
    SELECT
        -- Die Meldung hat beim Publisher keine stabile ID, link kommt für dieselbe Meldung in
        -- mehreren Formen vor. Titel und Beginn zusammen bezeichnen ein Ereignis.
        TO_HEX(MD5(CONCAT(title, '|', COALESCE(startdatetime, '')))) AS alert_id,
        title,
        -- 2 ist eine Störung, 5 die Entwarnung ("Service resumed"). CAST statt SAFE_CAST: steht
        -- dort einmal keine Zahl, soll der Lauf abbrechen, statt still NULL zu schreiben.
        CAST(type AS INT64) AS message_type,
        TIMESTAMP(published) AS published_at,
        TIMESTAMP(PARSE_DATETIME('%Y-%m-%dT%H:%M:%S', SUBSTR(startdatetime, 1, 19)), 'Europe/Zurich') AS start_at,
        TIMESTAMP(PARSE_DATETIME('%Y-%m-%dT%H:%M:%S', SUBSTR(enddatetime, 1, 19)), 'Europe/Zurich') AS end_at,
        TRIM(REGEXP_REPLACE(REGEXP_REPLACE(description_html, r'<br\s*/?>', ' '), r'<[^>]+>', '')) AS text,
        link,
        author,
        _PARTITIONDATE AS published_day
    FROM {{ source('alerts', 'alerts') }}
    WHERE _PARTITIONDATE BETWEEN DATE '{{ var("alerts_from", "2026-10-01") }}'
        AND DATE '{{ var("alerts_to", "2026-10-31") }}'
)

SELECT
    alert_id,
    title,
    message_type,
    published_at,
    start_at,
    end_at,
    text,
    link,
    author,
    published_day,
    -- Wie oft der Publisher die Meldung nachgeführt hat. Nur zur Information.
    COUNT(*) OVER (PARTITION BY alert_id) AS n_updates
FROM rows_in_window
-- Pro Meldung nur die neueste Fassung.
QUALIFY ROW_NUMBER() OVER (PARTITION BY alert_id ORDER BY published_at DESC) = 1
