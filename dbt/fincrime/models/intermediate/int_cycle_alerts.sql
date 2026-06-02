{{ config(materialized='view') }}

with transactions as (
    select distinct
        src_account_id,
        dst_account_id
    from {{ ref('stg_ibm_aml__transactions') }}
),

-- Find reciprocal pairs: A sends to B AND B sends to A
reciprocal as (
    select
        t1.src_account_id                            as account_id,
        count(*)                                     as reciprocal_count
    from transactions t1
    inner join transactions t2
        on t1.src_account_id = t2.dst_account_id
        and t1.dst_account_id = t2.src_account_id
    group by t1.src_account_id
),

laundering_lookup as (
    select
        src_account_id as account_id,
        max(is_laundering::integer) as any_laundering
    from {{ ref('stg_ibm_aml__transactions') }}
    group by src_account_id
),

alerts as (
    select
        r.account_id,
        'cycle'                                      as rule_name,
        r.reciprocal_count                           as metric_value,
        round(r.reciprocal_count / 2.0, 2)           as severity,
        case when l.any_laundering > 0
            then true else false end                 as ground_truth_label
    from reciprocal r
    left join laundering_lookup l on r.account_id = l.account_id
    where r.reciprocal_count >= 2
)

select * from alerts
