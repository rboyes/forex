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
    updated_at
from {{ ref("staging_rates") }}
{% if is_incremental() %}
where updated_at > (
    select coalesce(max(updated_at), timestamp '1900-01-01')
    from {{ this }}
)
{% endif %}
