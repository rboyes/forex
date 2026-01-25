
select *
from `forex-20260115`.`staging`.`rates`
where date > current_date()
