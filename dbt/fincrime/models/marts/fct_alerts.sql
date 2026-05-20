{{ config(materialized='table') }}

/*
  fct_alerts — the system's canonical alerts table.

  Source: int_account_transaction_features (aggregated per source account).
  Logic: applies fan-out threshold from the rules engine to produce alerts.

  This is a simplified Week 2 implementation — produces alerts for the
  fan-out typology only. In Week 3, this model will be expanded to
  consolidate all four rule outputs (fan-out, fan-in, cycle, velocity)
  and join with ML scoring features.

  Materialised as a table because:
    - Queried repeatedly by Power BI, Streamlit, and the ML model
    - Expensive to compute (joins + aggregations across 5M rows)
    - Stable between dbt runs (only changes when source data changes)
*/

with account_features as (
    select * from {{ ref('int_account_transaction_features') }}
),

fan_out_alerts as (
    select
        -- Deterministic alert ID (same pattern as your Python rules)
        'fan_out_' || substring(md5(account_id), 1, 6) as alert_id,
        'fan_out'                                      as rule_name,
        account_id,
        unique_destinations                            as destination_count,
        total_amount_sent                              as total_amount,
        first_txn_at                                   as window_start,
        last_txn_at                                    as window_end,
        round(unique_destinations / 8.0, 2)            as severity,
        is_laundering_account                          as ground_truth_label
    from (
        select
            *,
            case when laundering_txn_count > 0 then true else false end
                as is_laundering_account
        from account_features
        where unique_destinations >= 8  -- Same threshold as fan_out.py
    )
),

final as (
    select
        alert_id,
        rule_name,
        account_id,
        rule_name || '_' || account_id as alert_key,  -- composite for uniqueness
        destination_count,
        total_amount,
        window_start,
        window_end,
        severity,
        ground_truth_label,
        current_timestamp              as generated_at
    from fan_out_alerts
)

select * from final
