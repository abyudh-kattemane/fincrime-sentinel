{{ config(materialized='table') }}

with features as (
    select * from {{ ref('int_account_transaction_features') }}
)

select
    account_id,
    total_txn_sent,
    total_amount_sent,
    unique_destinations_sent,
    unique_currencies_sent,
    unique_payment_methods_sent,
    active_days_sent,
    first_txn_sent_at,
    last_txn_sent_at,
    total_txn_received,
    total_amount_received,
    unique_sources_received,
    active_days_received,
    first_txn_received_at,
    last_txn_received_at,
    send_receive_ratio,
    case when total_txn_sent > 0 then true else false end  as is_sender,
    case when total_txn_received > 0 then true else false end as is_receiver,
    case when is_laundering_involved > 0 then true else false end as is_laundering_account
from features
