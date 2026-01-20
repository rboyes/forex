{% macro ensure_raw_rates_external() %}
  {% if target.type == "bigquery" %}
    {% set gcs_uri = var("raw_rates_gcs_uri") %}
    {% set sql %}
      create external table if not exists `{{ target.project }}.raw.rates` (
        base_iso STRING,
        to_iso STRING,
        date DATE,
        rate FLOAT64,
        updated_at TIMESTAMP
      )
      options (
        format = 'NEWLINE_DELIMITED_JSON',
        uris = ['{{ gcs_uri }}']
      )
    {% endset %}
    {% do run_query(sql) %}
  {% endif %}
{% endmacro %}
