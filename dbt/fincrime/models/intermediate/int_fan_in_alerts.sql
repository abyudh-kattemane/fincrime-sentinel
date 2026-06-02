{{ config(materialized='view') }}

with transactions as (
    select * from {{ ref('stg_ibm_aml__transactions') }}
),

-- Aggregate by DESTINATION account (the receiver)
dst_aggregates as (
    select
        dst_account_id                               as account_id,
        count(distinct src_account_id)               as unique_sources,
        max(is_laundering::integer)                  as any_laundering
    from transactions
    group by dst_account_id
),

alerts as (
    select
        account_id,
        'fan_in'                                     as rule_name,
        unique_sources                               as metric_value,
        round(unique_sources / 8.0, 2)               as severity,
        case when any_laundering > 0
            then true else false end                 as ground_truth_label
    from dst_aggregates
    where unique_sources >= 8
)

select * from alerts
