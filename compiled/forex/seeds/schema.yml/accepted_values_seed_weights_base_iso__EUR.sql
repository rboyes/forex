
    
    

with all_values as (

    select
        base_iso as value_field,
        count(*) as n_records

    from `forex-20260115`.`staging`.`seeds`
    group by base_iso

)

select *
from all_values
where value_field not in (
    'EUR'
)


