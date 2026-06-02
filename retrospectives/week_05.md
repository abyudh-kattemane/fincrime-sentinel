## Day 14 — Tuesday 02 June (dbt backfill)

What I did:
– Built int_fan_in/cycle/velocity alert models, refactored fct_alerts to UNION ALL four rules
– Built dim_accounts as complete entity registry (senders + receivers)
– Tuned cycle and velocity thresholds across multiple passes

What I learned:
– UNION ALL over UNION for performance and never-silently-drop safety
– Dimensions must be complete entity registries — the relationships test caught 277 receiver-only accounts missing from dim_accounts
– Threshold tuning is iterative configuration, not fixed law
– Rolling-window counts (Python) produce account-window rows; full-window (dbt) produces account rows — explains count differences

What went wrong:
– First dim_accounts only had senders, broke the relationships test on fan_in alerts
– Threshold tuning overcorrected twice before landing in operational range
