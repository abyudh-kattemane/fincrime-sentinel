{{ config(materialized='view') }}

with features as (
    select * from {{ ref('int_account_transaction_features') }}
),

alerts as (
    select
        account_id,
        'velocity'                                   as rule_name,
        avg_daily_txn_sent                          as metric_value,
        round(avg_daily_txn_sent / 20.0, 2)         as severity,
        case when laundering_txn_count_sent > 0
            then true else false end                 as ground_truth_label
    from features
    -- High daily transaction rate: 20+ transactions per active day
    where avg_daily_txn_sent >= 20
)

select * from alerts
