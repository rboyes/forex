

select
    base_iso,
    to_iso,
    date,
    rate,
    created_at,
    updated_at
from `forex-20260115`.`staging`.`rates`

where updated_at > (
    select coalesce(max(updated_at), timestamp '1900-01-01')
    from `forex-20260115`.`presentation`.`rates`
)
