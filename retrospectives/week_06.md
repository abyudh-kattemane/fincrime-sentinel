## Day 16 — Monday 15 June Architectural update: two-sided feature model

What I did:
– Identified an architectural gap: int_account_transaction_features was source-grain only, so fan-in aggregated independently from staging and the ML target was sender-biased
– Rebuilt the features model two-sided on a branch: complete account universe (senders + receivers), mirrored sender/receiver aggregates, send_receive_ratio for pass-through detection, involvement-based laundering label
– Switched the ML target from sender-only laundering to laundering involvement (either direction)
– Refactored fan_in to read from the features model; simplified dim_accounts to a thin select; re-exported features.parquet; retrained, recalibrated, re-SHAP'd

What I learned:
– A shared upstream model gets shaped by whichever consumer is built first. The features model was built for the ML model + fan_out (both source-grain), so it was one-sided. Periodically check shared models against ALL consumers, not just today's
– Changing the target changes the question: involvement is a harder, broader, more correct problem than sender-only. Class balance moved 0.68% → 1.23%
– Aggregate PR-AUC dropped (0.46 → 0.37) — the honest cost of the harder target. But Precision@K, the operational metric, improved: top-500 56% → 72%, top-1000 32% → 41%, with top-50/100 holding at 100%
– SHAP confirmed the rebuild paid off: active_days_received became the #1 feature, send_receive_ratio ranked #3. The most predictive features were ones the old model couldn't see
– Judge a model on the metric that matches its use, not the one that flatters. A lower PR-AUC with higher Precision@K is a win for a ranked-queue system

Key principle: spotting an architectural flaw, fixing it properly, and evaluating honestly on the right metric is the difference between code that works and engineering judgement.
