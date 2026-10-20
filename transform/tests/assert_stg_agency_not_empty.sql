-- Schützt davor, dass agency_pattern nichts mehr trifft, etwa weil die Agentur im Feed umbenannt wurde.
-- Dann wären alle Modelle danach leer, und der Mart würde still "keine Fahrten" melden statt zu scheitern.
-- Ein Singular-Test schlägt fehl, sobald die Abfrage eine Zeile liefert.

SELECT 'stg_agency ist leer' AS problem
FROM (SELECT COUNT(*) AS n FROM {{ ref('stg_agency') }})
WHERE n = 0
