{{ config(materialized='table') }}

with all_rule_alerts as (
    select * from {{ ref('int_fan_out_alerts') }}
    union all
    select * from {{ ref('int_fan_in_alerts') }}
    union all
    select * from {{ ref('int_velocity_alerts') }}
    union all
    select * from {{ ref('int_cycle_alerts') }}
),

final as (
    select
        'alert_' || rule_name || '_' || substring(md5(account_id), 1, 6) as alert_id,
        rule_name,
        account_id,
        rule_name || '_' || account_id               as alert_key,
        metric_value,
        severity,
        ground_truth_label,
        current_timestamp                            as generated_at
    from all_rule_alerts
)

select * from final
