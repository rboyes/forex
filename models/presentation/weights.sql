{{ config(
    materialized="table",
    schema="presentation"
) }}

select
    base_iso,
    to_iso,
    weight
from {{ ref("seed_weights") }}
