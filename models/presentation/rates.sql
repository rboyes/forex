{{ config(
    materialized="incremental",
    unique_key=["base_iso", "to_iso", "date"],
    schema="presentation"
) }}

select
    base_iso,
    to_iso,
    date,
    rate,
    {{ dbt.current_timestamp() }} as updated_at
from {{ source("staging", "rates") }}
{% if is_incremental() %}
where date > (
    select coalesce(max(date), date '1900-01-01')
    from {{ this }}
)
{% endif %}
