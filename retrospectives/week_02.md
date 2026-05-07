## Day 5 - Monday 4 May

**Done:**
- Fan-out detector implemented in src/rules/fan_out.py with full docstring
- 8 unit tests covering happy path, edge cases, and boundary conditions
- Rule evaluated against full IBM dataset:
  * 7345 alerts generated
  * Precision: 3.1%, Recall: 6.7%
- First Python module written for the project (template for the other 3 rules)

**Learned:**
- Writing the function signature and docstring before the implementation
  forces design clarity — you can't write a clear docstring for a confused
  function
- The keyword-only argument trick (the `*` in the signature) makes calls
  self-documenting at the call site
- Defensive checks at the function boundary catch bad inputs early with
  a clear error message — much better than crashing 200 lines deep
- One rule alone has low precision; this is the structural reason ML
  scoring exists in the architecture

## Day 6 — Tuesday 5 May (afternoon)

What I did:
– fan_in.py, cycle.py, velocity.py — same skeleton as fan_out, different detection logic
– run_all_rules() consolidator with **kwargs pass-through per rule
– Combined evaluation: 81,749 alerts, 1.3% precision, 30.5% recall

What went wrong:
– Python run_all_rules() hung. Rolling window loops on 5M rows are O(n²). Killed it
– First DuckDB SQL attempt also hung — self-join across 5M rows is the same problem
  in SQL. DuckDB can't fix a quadratic algorithm
– Had to drop the rolling window for fan-out and fan-in in SQL. Count distinct
  destinations across the full 18-day dataset instead. This is why fan_out alerts
  jumped from 7,345 (Python, rolling) to 13,480 (SQL, full dataset)

What I learned:
– Cycle rule produced 62,898 of the 81,749 total alerts. Reciprocal flows are normal
  in legitimate transactions. ML scoring layer will need to learn to discount these
– Velocity only fired 142 times — 3-sigma against own baseline is the strictest test
– Recall jumped from 6.7% to 30.5% by adding three more typologies. Precision dropped
  from 3.1% to 1.3%. More rules = wider net = more debris.
