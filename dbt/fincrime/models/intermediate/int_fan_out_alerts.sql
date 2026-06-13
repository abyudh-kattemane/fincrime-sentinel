{{ config(materialized='view') }}

with features as (
    select * from {{ ref('int_account_transaction_features') }}
),

alerts as (
    select
        account_id,
        'fan_out'                                    as rule_name,
        unique_destinations_sent                         as metric_value,
        round(unique_destinations_sent / 8.0, 2)          as severity,
        case when laundering_txn_count_sent > 0
            then true else false end                 as ground_truth_label
    from features
    where unique_destinations_sent >= 8
)

select * from alerts
