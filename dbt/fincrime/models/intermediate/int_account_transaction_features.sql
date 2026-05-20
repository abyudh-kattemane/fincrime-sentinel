{{ config(materialized='view') }}

with transactions as (
    select * from {{ ref('stg_ibm_aml__transactions') }}
),

/*
  Compute per-account aggregate features over the full observation window.
  These feed the ML scoring layer as training features and inference inputs.

  Note: full-window aggregation (not rolling) is used here for simplicity.
  The ML model handles temporal generalisation via its train/test split.
*/

account_aggregates as (
    select
        src_account_id                              as account_id,

        -- Volume features
        count(*)                                    as total_txn_count,
        sum(amount)                                 as total_amount_sent,
        avg(amount)                                 as avg_amount_sent,
        stddev(amount)                              as stddev_amount_sent,
        max(amount)                                 as max_single_txn,
        min(amount)                                 as min_single_txn,

        -- Counterparty diversity (fan-out signal)
        count(distinct dst_account_id)              as unique_destinations,

        -- Temporal features
        min(txn_timestamp)                          as first_txn_at,
        max(txn_timestamp)                          as last_txn_at,
        datediff('day', min(txn_timestamp),
                        max(txn_timestamp))         as active_days,

        -- Currency and method diversity
        count(distinct currency)                    as unique_currencies,
        count(distinct payment_method)              as unique_payment_methods,

        -- Laundering rate (for training — not available at inference time)
        avg(is_laundering::integer)                 as laundering_rate,
        sum(is_laundering::integer)                 as laundering_txn_count

    from transactions
    group by src_account_id
),

/*
  Derived features: ratios and normalised values computed from aggregates.
  Separating derivations from aggregations keeps the logic auditable.
*/

enriched as (
    select
        account_id,

        -- Raw aggregates
        total_txn_count,
        total_amount_sent,
        avg_amount_sent,
        stddev_amount_sent,
        max_single_txn,
        min_single_txn,
        unique_destinations,
        first_txn_at,
        last_txn_at,
        active_days,
        unique_currencies,
        unique_payment_methods,
        laundering_rate,
        laundering_txn_count,

        -- Derived ratios
        case when active_days > 0
            then total_txn_count / active_days
            else null
        end                                         as avg_daily_txn_count,

        case when total_txn_count > 0
            then unique_destinations / total_txn_count::float
            else null
        end                                         as destination_diversity_ratio,

        case when total_txn_count > 0
            then laundering_txn_count / total_txn_count::float
            else null
        end                                         as laundering_ratio

    from account_aggregates
)

select * from enriched
