# Week 1 Retrospective

## Day 1 - Sunday 26 April

What I did:
- Set up the repo with uv and pre-commit
- Got CI working on first push (took longer than I expected)
- Wrote the README
- 7 commits

What I learned:
- pyproject.toml does a lot. ruff config, dependencies, pytest config all in one file
- pre-commit "Failed" usually just means it auto-fixed something. re-stage and try again
- Most junior portfolios skip CI. mine has it from day 1, that's a real differentiator

Things that took longer than expected:
- Getting pre-commit and ruff to play nice with the empty notebook file. CI kept failing
  because ruff couldn't parse an empty .ipynb as JSON. fixed by scoping ruff to src/ and
  tests/ only

## Day 2 - Wednesday 29 April

What I did:
- Set up the Drive folder structure
- Wrote the bootstrap cell that downloads the Kaggle dataset

What went wrong:
- Downloaded the whole 7.6GB dataset by accident and filled my Drive. Only need the
  HI-Small files (500MB total). Need the -f flag in the kaggle command to filter

What I learned:
- Bootstrap cells follow a pattern: imports, paths, folders, auth, install, fetch, verify
- Use pathlib.Path for paths, not strings. ALL_CAPS for constants

## Day 3 - Thursday 30 April

What I did:
- CSV to Parquet conversion (467MB CSV becomes 110MB Parquet, way faster reads)
- Documented all 11 columns
- Found a bunch of stuff in the data

The headline number: 0.102% laundering rate. 5,177 out of 5.08M transactions.
This is the number I'm anchoring everything else against.

Other findings:
- Median txn $1,411. Mean is $5.99M because of one trillion-dollar outlier
- The trillion-dollar txn is real, IBM put it there. NOT laundering. NOT a dtype bug
  (I thought it was a float32 problem at first, switched to float64, still trillion)
- 30,470 sender banks but only 15,811 receivers. Money flows toward fewer hubs
- 93% of account IDs are hex strings. Must store as string

Things I want to remember:
- Don't drop outliers without a reason. They're data, not errors
- Median not mean for heavy-tailed money distributions
- DuckDB SQL is much faster than pandas groupby for aggs on 5M rows

Painful bit: had to commit "feat(eda): convert CSV to Parquet..." three times because
of push rejections. Got tangled with old Colab commits. Sorted now.

## Day 4 - Friday 1 May

Spent the whole day untangling Git problems instead of doing data analysis.

What broke:
- nbqa-ruff kept failing on F821 (undefined name 'PROCESSED'). It's a false positive,
  the variable is defined in an earlier cell, but ruff analyses cells in isolation.
  Fixed by adding F821 to per-file-ignores for notebooks/* in pyproject.toml
- Notebook wouldn't render on GitHub - "Invalid Notebook". Colab adds widget metadata
  that breaks GitHub's renderer. Wrote clean_notebook.py to strip it
- Local and origin/main got out of sync because Colab's "Save a copy in GitHub" was
  pushing while I was also pushing from my Mac. Two paths to origin = trouble

What fixed it:
- Hard reset to origin/main, save my changes externally, restore them on top
- Stop using Colab's GitHub save feature. Download .ipynb, run cleanup script,
  commit from Mac

Lessons:
- One push path, not two. Pick Mac, stick with Mac
- Generated files (notebooks have widget metadata) are different from source files.
  When they diverge, re-derive instead of merge.

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
