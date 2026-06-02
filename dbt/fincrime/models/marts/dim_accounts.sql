{{ config(materialized='table') }}

with senders as (
    select distinct src_account_id as account_id
    from {{ ref('stg_ibm_aml__transactions') }}
),

receivers as (
    select distinct dst_account_id as account_id
    from {{ ref('stg_ibm_aml__transactions') }}
),

-- Complete account universe: anything that sent OR received
all_accounts as (
    select account_id from senders
    union
    select account_id from receivers
),

sender_features as (
    select * from {{ ref('int_account_transaction_features') }}
),

-- Laundering label: account is laundering if ANY transaction involving it is laundering,
-- whether they sent or received
laundering_involvement as (
    select
        account_id,
        max(any_laundering) as is_laundering
    from (
        select
            src_account_id as account_id,
            max(is_laundering::integer) as any_laundering
        from {{ ref('stg_ibm_aml__transactions') }}
        group by src_account_id

        union all

        select
            dst_account_id as account_id,
            max(is_laundering::integer) as any_laundering
        from {{ ref('stg_ibm_aml__transactions') }}
        group by dst_account_id
    ) combined
    group by account_id
)

select
    aa.account_id,
    coalesce(sf.total_txn_count, 0)         as total_txn_count_sent,
    coalesce(sf.total_amount_sent, 0)       as total_amount_sent,
    coalesce(sf.unique_destinations, 0)     as unique_destinations,
    coalesce(sf.unique_currencies, 0)       as unique_currencies,
    coalesce(sf.unique_payment_methods, 0)  as unique_payment_methods,
    coalesce(sf.active_days, 0)             as active_days,
    sf.first_txn_at,
    sf.last_txn_at,
    case when sf.account_id is not null
        then true else false end             as is_sender,
    case when li.is_laundering > 0
        then true else false end             as is_laundering_account
from all_accounts aa
left join sender_features sf
    on aa.account_id = sf.account_id
left join laundering_involvement li
    on aa.account_id = li.account_id
