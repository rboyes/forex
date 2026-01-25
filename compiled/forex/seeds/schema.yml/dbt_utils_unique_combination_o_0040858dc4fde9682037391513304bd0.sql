





with validation_errors as (

    select
        base_iso, to_iso
    from `forex-20260115`.`staging`.`seeds`
    group by base_iso, to_iso
    having count(*) > 1

)

select *
from validation_errors


