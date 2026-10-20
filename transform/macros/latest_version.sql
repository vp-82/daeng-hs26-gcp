{#-
    Gibt die neueste Feed-Version in raw als Datumsliteral zurück, zum Beispiel DATE '2026-10-17'.

    raw hält mehrere Versionen nebeneinander, eine pro Partition. Läsen wir alle, käme jede Fahrt
    einmal pro Version vor. Die Version wird beim Kompilieren abgefragt und als fester Wert ins SQL
    geschrieben, denn nur bei einem festen Wert liest BigQuery allein diese eine Partition. Mit einer
    Unterabfrage (WHERE _PARTITIONDATE = (SELECT MAX(...))) würde BigQuery alle Partitionen lesen.
-#}
{% macro latest_version() %}
    {#- Ausserhalb von "if execute", damit dbt feed_info beim Parsen als Quelle des Modells erkennt (Lineage). -#}
    {%- set feed_info = source('raw', 'feed_info') -%}
    {%- if execute -%}
        {#- Nur die Pseudo-Spalte _PARTITIONDATE: BigQuery beantwortet das aus den Metadaten, 0 Bytes. -#}
        {%- set result = run_query("SELECT CAST(MAX(_PARTITIONDATE) AS STRING) FROM " ~ feed_info) -%}
        {%- set version = result.columns[0].values()[0] -%}
        {%- if version is none -%}
            {{ exceptions.raise_compiler_error("raw.feed_info hat keine Partition, es gibt keine Version zum Verarbeiten") }}
        {%- endif -%}
        {{ log("Feed-Version " ~ version ~ " für " ~ model.name, info=true) }}
        DATE '{{ version }}'
    {%- else -%}
        {#- Beim Parsen fragt dbt nichts ab; der Platzhalter wird nie ausgeführt. -#}
        DATE '1970-01-01'
    {%- endif -%}
{% endmacro %}
