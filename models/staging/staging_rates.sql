{{ config(
    materialized="incremental",
    unique_key=["base_iso", "to_iso", "date"],
    incremental_strategy="merge",
    schema="staging",
    alias="rates"
) }}

with deduped as (
    select
        base_iso,
        to_iso,
        date,
        rate,
        updated_at,
        row_number() over (
            partition by base_iso, to_iso, date
            order by updated_at desc
        ) as row_number_rank
    from {{ source("raw", "rates") }}
)
select
    base_iso,
    to_iso,
    date,
    rate,
    updated_at
from deduped
where row_number_rank = 1
