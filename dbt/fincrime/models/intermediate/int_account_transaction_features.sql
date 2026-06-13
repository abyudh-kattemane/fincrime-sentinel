{{ config(materialized='view') }} -- store model as a view

with transactions as (
    select * from {{ ref('stg_ibm_aml__transactions') }} -- select everything from the staged transactions model
),

-- get all unique accounts that either sent or received money
all_accounts as (
    select distinct src_account_id as account_id from transactions
    union
    select distinct dst_account_id as account_id from transactions
),

/*
  Compute per-account aggregate features over the full observation window.
  These feed the ML scoring layer as training features and inference inputs.

  Note: full-window aggregation (not rolling) is used here for simplicity.
  The ML model handles temporal generalisation via its train/test split.
*/

/*
  Sender-side aggregates: features computed by grouping on the source account (the sender).
  These capture the behaviour of accounts when they send money.
*/

sender_agg as (
    select
        src_account_id                              as account_id,

        -- Volume features
        count(*)                                    as total_txn_sent,
        sum(amount)                                 as total_amount_sent,
        avg(amount)                                 as avg_amount_sent,
        stddev(amount)                              as stddev_amount_sent,
        max(amount)                                 as max_single_txn_sent,
        min(amount)                                 as min_single_txn_sent,

        -- Counterparty diversity (fan-out signal)
        count(distinct dst_account_id)              as unique_destinations_sent,

        -- Temporal features
        min(txn_timestamp)                          as first_txn_sent_at,
        max(txn_timestamp)                          as last_txn_sent_at,
        datediff('day', min(txn_timestamp),
                        max(txn_timestamp))         as active_days_sent,

        -- Currency and method diversity
        count(distinct currency)                    as unique_currencies_sent,
        count(distinct payment_method)              as unique_payment_methods_sent,

        -- Laundering rate (for training — not available at inference time)
        avg(is_laundering::integer)                 as laundering_rate_sent,
        sum(is_laundering::integer)                 as laundering_txn_count_sent

    from transactions
    group by src_account_id
),

/*
  Compute per account aggregates for accounts that only receive (no outgoing transactions).
  This ensures that the final feature set has values for all accounts, even those that never send money.
*/

receiver_agg as (
    select
        dst_account_id                              as account_id,
        count(*)                                    as total_txn_received,
        sum(amount)                                 as total_amount_received,
        avg(amount)                                 as avg_amount_received,
        stddev(amount)                              as stddev_amount_received,
        max(amount)                                 as max_single_txn_received,
        min(amount)                                 as min_single_txn_received,
        count(distinct src_account_id)              as unique_sources_received,
        min(txn_timestamp)                          as first_txn_received_at,
        max(txn_timestamp)                          as last_txn_received_at,
        datediff('day', min(txn_timestamp),
                        max(txn_timestamp))         as active_days_received,
        count(distinct currency)                    as unique_currencies_received,
        count(distinct payment_method)              as unique_payment_methods_received,
        avg(is_laundering::integer)                 as laundering_rate_received,
        sum(is_laundering::integer)                 as laundering_txn_count_received
    from transactions
    group by dst_account_id
),

-- capture whether an account is involved in laundering at all, whether as sender or receiver
laundering_involvement as (
    select account_id, max(any_laundering) as is_laundering_involved
    from (
        select src_account_id as account_id, max(is_laundering::integer) as any_laundering
        from transactions group by src_account_id
        union all
        select dst_account_id as account_id, max(is_laundering::integer) as any_laundering
        from transactions group by dst_account_id
    ) combined
    group by account_id
),

/*
  Derived features: ratios and normalised values computed from aggregates.
  Separating derivations from aggregations keeps the logic auditable.
*/

enriched as (
    select
        aa.account_id,

        -- Sender aggregates
        coalesce(sf.total_txn_sent, 0)               as total_txn_sent,   -- using coalesce to fill in zeros for accounts with no outgoing transactions
        coalesce(sf.total_amount_sent, 0)            as total_amount_sent,
        coalesce(sf.avg_amount_sent, 0)              as avg_amount_sent,
        coalesce(sf.stddev_amount_sent, 0)           as stddev_amount_sent,
        coalesce(sf.max_single_txn_sent, 0)          as max_single_txn_sent,
        coalesce(sf.min_single_txn_sent, 0)          as min_single_txn_sent,
        coalesce(sf.unique_destinations_sent, 0)     as unique_destinations_sent,
        sf.first_txn_sent_at,
        sf.last_txn_sent_at,
        coalesce(sf.active_days_sent, 0)             as active_days_sent,
        coalesce(sf.unique_currencies_sent, 0)       as unique_currencies_sent,
        coalesce(sf.unique_payment_methods_sent, 0)  as unique_payment_methods_sent,
        sf.laundering_rate_sent,
        coalesce(sf.laundering_txn_count_sent, 0)    as laundering_txn_count_sent,
        -- Sender Derived ratios
        case when active_days_sent > 0
            then total_txn_sent / active_days_sent
            else null
        end                                          as avg_daily_txn_sent,

        case when total_txn_sent > 0
            then unique_destinations_sent / total_txn_sent::float
            else null
        end                                          as destination_diversity_ratio_sent,

        case when total_txn_sent > 0
            then laundering_txn_count_sent / total_txn_sent::float
            else null
        end                                          as laundering_ratio_sent,

        -- Receiver aggregates
        coalesce(rf.total_txn_received, 0)           as total_txn_received,
        coalesce(rf.total_amount_received, 0)        as total_amount_received,
        coalesce(rf.avg_amount_received, 0)          as avg_amount_received,
        coalesce(rf.stddev_amount_received, 0)       as stddev_amount_received,
        coalesce(rf.max_single_txn_received, 0)      as max_single_txn_received,
        coalesce(rf.min_single_txn_received, 0)      as min_single_txn_received,
        coalesce(rf.unique_sources_received, 0)      as unique_sources_received,
        rf.first_txn_received_at,
        rf.last_txn_received_at,
        coalesce(rf.active_days_received, 0)         as active_days_received,
        coalesce(rf.unique_currencies_received, 0)   as unique_currencies_received,
        coalesce(rf.unique_payment_methods_received, 0) as unique_payment_methods_received,
        rf.laundering_rate_received,
        coalesce(rf.laundering_txn_count_received, 0)   as laundering_txn_count_received,
        -- Receiver Derived ratios
        case when active_days_received > 0
            then total_txn_received / active_days_received
            else null
        end                                          as avg_daily_txn_received,

        case when total_txn_received > 0
            then unique_sources_received / total_txn_received::float
            else null
        end                                          as source_diversity_ratio_received,

        case when total_txn_received > 0
            then laundering_txn_count_received / total_txn_received::float
            else null
        end                                          as laundering_ratio_received,

        case when coalesce(rf.total_amount_received, 0) > 0
            then coalesce(sf.total_amount_sent, 0) / rf.total_amount_received
            else null
        end                                          as send_receive_ratio,

        -- laundering involvement (sender or receiver)
        coalesce(li.is_laundering_involved, 0)       as is_laundering_involved

    from all_accounts aa
    left join sender_agg sf on aa.account_id = sf.account_id
    left join receiver_agg rf on aa.account_id = rf.account_id
    left join laundering_involvement li on aa.account_id = li.account_id
) -- final CTE combining all features together

select * from enriched
