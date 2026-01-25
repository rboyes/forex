
    
    

with all_values as (

    select
        to_iso as value_field,
        count(*) as n_records

    from `forex-20260115`.`staging`.`seeds`
    group by to_iso

)

select *
from all_values
where value_field not in (
    'GBP','USD','NZD','CAD','AUD','JPY','CNY'
)


