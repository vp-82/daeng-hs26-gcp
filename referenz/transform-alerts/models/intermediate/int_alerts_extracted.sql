-- Hier liest das Sprachmodell. Aus dem Text einer Störungsmeldung werden Fakten: Ursache,
-- Auswirkung, Abschnitt, Linie, Beginn, Ende, Schweregrad. Das Modell entscheidet nichts, es
-- füllt Spalten. Was mit den Spalten geschieht, steht in alert_decisions und ist eine Regel.
--
-- Drei Entscheidungen in diesem Modell sind Data Engineering, nicht KI:
-- 1. Vorauswahl mit einer Regel. Das Modell liest nur Störungen (message_type 2), die einen
--    Bahnhof aus der Seed-Tabelle nennen. Alles andere kann die Verkehrsbetriebe Luzern nicht
--    betreffen, und jeder Aufruf kostet Zeit und Geld.
-- 2. Inkrementell mit Gedächtnis. Eine Meldung, die schon extrahiert ist, wird nie wieder
--    extrahiert. Zwei Aufrufe mit demselben Text liefern nicht immer dasselbe Ergebnis, auch
--    bei Temperatur 0. Eine Meldung soll aber in der Pipeline nur einmal ihre Fakten bekommen,
--    sonst ändert sich die Entscheidung von Lauf zu Lauf, ohne dass sich die Welt geändert hat.
--    Darum MERGE auf alert_id, und nur Zeilen mit gültigem Ergebnis werden gemerkt. Fehlschläge
--    versucht der nächste Lauf nochmals.
-- 3. Das Modell ist festgeschrieben. gemini-3.8-flash hat keine datierte Version, darum steht
--    die ID hier und model_version wird mitgeschrieben. Ändert Google das Modell, sieht man es.
--
-- Die Verbindung heisst vertex-ai und liegt in europe-west6 neben den Daten. Das Modell rechnet
-- in der EU-Multiregion (die URL sagt es), weil Gemini in Zürich nicht verfügbar ist. Die Daten
-- bleiben in Zürich, nur der Prompt geht in die EU.

{{ config(
    materialized='incremental',
    unique_key='alert_id'
) }}

WITH candidates AS (
    SELECT a.alert_id, a.title, a.text
    FROM {{ ref('stg_alerts') }} AS a
    WHERE a.message_type = 2
        -- Vorauswahl: ein Bahnhofname aus der Seed-Tabelle als ganzes Wort in Titel oder Text.
        -- Alle Namen in einem Ausdruck (Luzern|Emmenbrücke|...), weil BigQuery in einem EXISTS
        -- keine Regex-Bedingung erlaubt.
        AND REGEXP_CONTAINS(
            CONCAT(a.title, ' ', a.text),
            CONCAT(
                r'(^|[^\p{L}])(',
                (SELECT STRING_AGG(b.bahnhof, '|') FROM {{ ref('vbl_bahnhoefe') }} AS b),
                r')([^\p{L}]|$)'
            )
        )
    {% if is_incremental() %}
        -- Gedächtnis: was schon in der Tabelle steht, wird nicht nochmals gelesen.
        AND a.alert_id NOT IN (SELECT alert_id FROM {{ this }})
    {% endif %}
),

extracted AS (
    SELECT
        c.alert_id,
        AI.GENERATE(
            (
                'You extract structured facts from a Swiss railway disruption message (SBB). ',
                'Use only what the text says. Station names exactly as written in the text. ',
                'Times in the text are Swiss local time, return them unchanged as YYYY-MM-DD HH:MM:SS. ',
                'Title: ', c.title, '\nText: ', c.text
            ),
            connection_id => '{{ target.project }}.europe-west6.{{ var("vertex_connection", "vertex-ai") }}',
            endpoint => 'https://aiplatform.eu.rep.googleapis.com/v1/projects/{{ target.project }}/locations/eu/publishers/google/models/{{ var("gemini_model", "gemini-3.8-flash") }}',
            -- Temperatur 0: so wenig Zufall wie möglich. Ganz weg ist er damit nicht.
            model_params => JSON '{"generation_config": {"temperature": 0}}',
            -- Zeitstempel sind im Schema nicht erlaubt, darum Text, der unten geparst wird.
            -- enum legt die erlaubten Werte fest, bevor das Modell antwortet.
            output_schema => """
                cause STRING NOT NULL OPTIONS(description = 'Cause of the disruption', `enum` = ['Bauarbeiten', 'technische Störung', 'Unfall', 'Unwetter', 'Fremdeinwirkung', 'unbekannt']),
                effect STRING NOT NULL OPTIONS(description = 'Main effect on train service', `enum` = ['Ausfall', 'Verspätung', 'Umleitung', 'Ersatzverkehr', 'Gleisänderung', 'Information']),
                section_from STRING OPTIONS(description = 'First station of the affected section "between A and B", if named'),
                section_to STRING OPTIONS(description = 'Second station of the affected section "between A and B", if named'),
                line_from STRING OPTIONS(description = 'First end of the railway line "on the X - Y line", if named'),
                line_to STRING OPTIONS(description = 'Second end of the railway line "on the X - Y line", if named'),
                begin STRING OPTIONS(description = 'Start of the disruption, the first time at the beginning of the text, YYYY-MM-DD HH:MM:SS'),
                `end` STRING OPTIONS(description = 'End of the disruption, the second time at the beginning of the text, YYYY-MM-DD HH:MM:SS'),
                lines ARRAY<STRING> OPTIONS(description = 'Affected train lines as written, e.g. IR15, S3'),
                replacement_bus BOOL NOT NULL OPTIONS(description = 'true if a replacement bus service is mentioned'),
                severity INT64 NOT NULL OPTIONS(description = '1 = delays only, 2 = limited service, 3 = interrupted service')
            """
        ) AS g
    FROM candidates AS c
)

SELECT
    alert_id,
    g.cause,
    g.effect,
    g.section_from,
    g.section_to,
    g.line_from,
    g.line_to,
    -- Die Zeiten im Text sind Lokalzeit, wie in stg_alerts.
    TIMESTAMP(SAFE.PARSE_DATETIME('%F %T', g.begin), 'Europe/Zurich') AS begin_at,
    TIMESTAMP(SAFE.PARSE_DATETIME('%F %T', g.`end`), 'Europe/Zurich') AS end_at,
    g.lines,
    g.replacement_bus,
    g.severity,
    -- Nachweis, welches Modell geantwortet hat und was es gekostet hat.
    JSON_VALUE(g.full_response, '$.model_version') AS model_version,
    SAFE_CAST(JSON_VALUE(g.full_response, '$.usage_metadata.prompt_token_count') AS INT64) AS prompt_tokens,
    SAFE_CAST(JSON_VALUE(g.full_response, '$.usage_metadata.candidates_token_count') AS INT64) AS output_tokens,
    CURRENT_TIMESTAMP() AS extracted_at
FROM extracted
-- Nur gültige Antworten. status ist leer, wenn der Aufruf gelungen ist.
WHERE COALESCE(g.status, '') = ''
