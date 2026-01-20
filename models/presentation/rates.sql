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
from {{ ref("staging_rates") }}
