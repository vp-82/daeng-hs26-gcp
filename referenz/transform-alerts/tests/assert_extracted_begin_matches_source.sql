-- Schützt vor erfundenen Zeiten. Der Publisher liefert den Beginn auch als Feld (startdatetime),
-- das Modell liest ihn aus dem Text. Beide müssen auf eine Stunde zusammenpassen. Weicht das
-- Modell weiter ab, hat es eine andere Zeit im Text für den Beginn gehalten, und dann ist auch
-- der Rest der Zeile verdächtig.

SELECT e.alert_id, a.start_at, e.begin_at
FROM {{ ref('int_alerts_extracted') }} AS e
JOIN {{ ref('stg_alerts') }} AS a USING (alert_id)
WHERE ABS(TIMESTAMP_DIFF(e.begin_at, a.start_at, MINUTE)) > 60
