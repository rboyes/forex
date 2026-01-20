{{ config(
    materialized="incremental",
    unique_key=["base_iso", "to_iso", "date"],
    schema="presentation",
    on_schema_change="append_new_columns"
) }}

select
    base_iso,
    to_iso,
    date,
    rate,
    created_at,
    updated_at
from {{ source("staging", "rates") }}
{% if is_incremental() %}
where updated_at > (
    select coalesce(max(updated_at), timestamp '1900-01-01')
    from {{ this }}
)
{% endif %}
