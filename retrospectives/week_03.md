## Day 7 — Tuesday 14 May (dbt scaffold)

What I did:
– Installed dbt-core and dbt-duckdb via uv
– Initialized fincrime dbt project, configured profiles.yml and dbt_project.yml inside the project (not in ~/.dbt/)
– Declared the IBM parquet as a source in _sources.yml
– Built first staging model stg_ibm_aml__transactions with two-CTE pattern (source then renamed)
– Set up materialization config: views for staging/intermediate, table for marts

What I learned:
– Medallion architecture isn't optional. Each layer has one job. Staging only cleans and types, intermediate joins and enriches, marts produce business-ready output
– Materialization choice is about query frequency, not computation cost. The mart gets hit 1000x a day so it's a table; intermediate only runs once per dbt build so it's a view
– dbt commands only work from the directory containing dbt_project.yml. Same rule as git from a .git/ repo
– ELT not ETL — load raw, transform in SQL via dbt

What went wrong
– The parquet was only in Google Drive (Colab was reading it from there), not on local Mac. Had to copy it across before dbt could read it. Local dev needs local data, obvious in hindsight

## Day 8 — Wednesday 20 May (staging tests + intermediate model + fct_alerts mart)

What I did:
– Added not_null tests on all key columns in staging
– Added accepted_values test on currency, which immediately failed
– Discovered the dataset has 15 distinct currencies including Shekel and Rupee, and the canonical form is 'US Dollar' singular not 'US Dollars' plural
– Built int_account_transaction_features as a view aggregating per source account
– Added unique test on account_id at the intermediate layer (grain column)
– Built fct_alerts as the canonical alerts table, materialized as a physical DuckDB table
– Translated the fan-out threshold logic from Python to SQL — same min_destinations=8, same severity formula
– Added relationships test as a foreign-key-style constraint (DuckDB doesn't enforce FKs natively, so the dbt test fills that gap)
– Declared accepted_values for rule_name with all 4 rule names even though only fan_out exists. Contract-first
– Verified: 13,480 alerts, 253 true positives, 1.88% precision

What I learned:
– A test that fails on first contact with real data is the test doing its job. Documentation tells you what should be there; SELECT DISTINCT tells you what is there. They diverge constantly
– Test the grain. Unique on account_id at intermediate is meaningful because the groupby should produce one row per account. Same test at staging would fail immediately because account_id appears once per transaction
– Per-account laundering rate (0.18%) and per-transaction laundering rate (0.8%) tell different stories. Picking the right metric is the difference between "this account looks bad" and "this transaction looks bad"
– ref() vs source(): source for data dbt didn't create, ref for models dbt did create. Two macros because they do different things — ref builds the DAG edge, source marks an external root
– The mart is the contract. Once Power BI and Streamlit point at fct_alerts, you can't casually change the schema without breaking dashboards
– Test what must be true, not what's likely true. alert_key (rule + full account_id) is unique by construction so test it. alert_id (rule + 6-char hash) is probably unique but could collide so don't test it
– Define the interface before all the producers exist. The accepted_values list with all 4 rule names means when I add fan_in tomorrow, naming inconsistencies fail at the test, not three layers downstream
– The 13,480 dbt count vs 7,345 Python count comes from windowing — dbt aggregates over the full 18 days, Python rolled over 10. Same threshold, different scope, more alerts but lower precision

What went wrong:
– Wasted time fixing the test the wrong way first. Updated the accepted_values list to add Shekel and Rupee, but missed that 'US Dollars' (plural) was also wrong. Two fixes when one careful query would have caught both
– Stuck on dbt 1.11 deprecation warning for ages because I added config: severity: warn instead of the actual fix which was nesting under arguments:

## Day 9 — Thursday 21 May (docs + CI)

What I did:
– Generated dbt docs and explored the lineage graph at localhost:8080
– Screenshot of the lineage graph saved for the README
– Added dbt verification step to GitHub Actions CI

What I learned:
– The lineage graph is auto-generated from ref() and source() calls. No manual drawing — dbt parses every model and builds the DAG by following the macros
– manifest.json is the project from code (intent), catalog.json is the physical reality from the warehouse (implementation). Both are needed because they answer different questions
– Three dbt commands run without a database connection: parse, list, debug. Everything else — run, test, compile, build — needs the warehouse
– parse builds the graph, run executes against it. Two different operations, same underlying structure

What went wrong:
– Tried dbt build in CI first, failed because CI has no DuckDB file or parquet
– Tried dbt parse + dbt compile next, compile also failed because it calls list_relations against the warehouse
– Ended up with dbt parse only. Three iterations to find the right command when the constraint ("CI has no database") could have led me straight to the answer
