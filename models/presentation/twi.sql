{{ config(
    materialized="incremental",
    unique_key=["base_iso", "date"],
    schema="presentation"
) }}

with base_rates as (
    select
        base_iso,
        date,
        avg(rate) as avg_rate
    from {{ ref("rates") }}
    group by 1, 2
),
recent_dates as (
    select
        base_iso,
        date,
        max(updated_at) as updated_at
    from {{ ref("rates") }}
    {% if is_incremental() %}
    where updated_at > (
        select coalesce(max(updated_at), timestamp '1900-01-01')
        from {{ this }}
    )
    {% endif %}
    group by 1, 2
),
base_dates as (
    select
        base_iso,
        min(date) as base_date
    from base_rates
    group by 1
),
base_values as (
    select
        br.base_iso,
        br.date,
        br.avg_rate,
        bd.base_date
    from base_rates br
    join base_dates bd
        on br.base_iso = bd.base_iso
),
base_index as (
    select
        bv.base_iso,
        bv.base_date,
        bv.avg_rate as base_avg_rate
    from base_values bv
    where bv.date = bv.base_date
),
twi_values as (
    select
        bv.base_iso,
        bv.date,
        (bv.avg_rate / bi.base_avg_rate) * 100.0 as rate,
        rd.updated_at as updated_at
    from base_values bv
    join base_index bi
        on bv.base_iso = bi.base_iso
    join recent_dates rd
        on bv.base_iso = rd.base_iso
        and bv.date = rd.date
)
select * from twi_values
