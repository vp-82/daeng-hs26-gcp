{#-
    Ohne dieses Makro hängt dbt ein custom schema an das Standard-Dataset an: aus +schema: marts
    würde staging_marts. Wir wollen genau die drei Datasets staging, intermediate und marts,
    deshalb nehmen wir das custom schema wörtlich.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
