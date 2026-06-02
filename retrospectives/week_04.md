## Day 10 — Monday 25 May (ML feature engineering)

What I did:
– Exported dbt intermediate features to parquet as the transformation-to-ML handoff
– Separated target from features, explicitly excluded leakage columns
– Stratified 80/20 split, saved 6 parquet files
– Confirmed class balance: 0.68% laundering (3,376 / 496,999)
– Saved X_train, X_test, y_train, y_test, ids_train, ids_test to Drive

What I learned:
– Target leakage is the most important ML concept I now know. Features derived from the label (laundering_rate, laundering_txn_count) can't be used because they don't exist at inference time. A model trained with these would hit 99% accuracy on training and fail in production
– Severe class imbalance (0.68%) means accuracy is meaningless. Have to use precision/recall/PR-AUC and stratified splits to keep both classes proportional
– Single source of truth: dbt computes the features, ML consumes via parquet. Don't reimplement the SQL in Colab. If I change feature logic, I change it once in dbt and re-export. Otherwise prod and analysis silently diverge

## Day 11 — Wednesday 27 May (XGBoost + calibration)

What I did:
– Trained XGBoost with scale_pos_weight=146.2; PR-AUC 0.46, ROC-AUC 0.93
– Precision@K: top-50 100%, top-100 100%, top-500 56%, top-1000 32%
– Calibrated with FrozenEstimator + isotonic; Brier 0.075 → 0.005

What I learned:
– scale_pos_weight is what makes the model learn the minority class
– PR-AUC over ROC-AUC for imbalanced data — ROC-AUC inflates via the FPR denominator
– The model is a ranker, not a classifier — work the queue top-down by probability
– XGBoost operates in log-odds space; sigmoid converts to probability

What went wrong:
– XGBoost 2.0.3 / sklearn 1.7 incompatibility (__sklearn_tags__), upgraded to 2.1.4
– cv='prefit' removed in sklearn 1.7, replaced with FrozenEstimator
– Two runtime restarts to pick up library changes

## Day 12 — Thursday 28 May (SHAP + comparison)

What I did:
– Computed SHAP via TreeExplainer; global, beeswarm, waterfall plots
– Built rules-vs-ML precision table: 3.1x to 5.3x lift at top operating points
– Saved artefacts to repo (figures + tables) and Drive (SHAP values for Week 4)

What I learned:
– unique_destinations dominant, total_txn_count least important: structure beats volume
– Top alert was a layering case (7 currencies, 15 active days), not fan-out — the ML layer catches what rules can't
– SHAP explains what the model learned, not what's true — synthetic data caveat matters
