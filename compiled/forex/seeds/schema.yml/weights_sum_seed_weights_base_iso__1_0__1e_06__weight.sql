
select
    base_iso as group_key,
    sum(weight) as total_weight
from `forex-20260115`.`staging`.`seeds`
group by 1
having abs(sum(weight) - 1.0) > 1e-06
