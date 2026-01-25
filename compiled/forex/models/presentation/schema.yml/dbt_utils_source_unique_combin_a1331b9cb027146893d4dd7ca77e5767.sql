





with validation_errors as (

    select
        base_iso, to_iso, date
    from `forex-20260115`.`staging`.`rates`
    group by base_iso, to_iso, date
    having count(*) > 1

)

select *
from validation_errors


