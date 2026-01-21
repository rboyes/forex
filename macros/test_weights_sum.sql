{% test weights_sum(model, weight_column, group_by, target_sum=1.0, tolerance=0.000001) %}
select
    {{ group_by }} as group_key,
    sum({{ weight_column }}) as total_weight
from {{ model }}
group by 1
having abs(sum({{ weight_column }}) - {{ target_sum }}) > {{ tolerance }}
{% endtest %}
