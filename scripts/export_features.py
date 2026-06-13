"""Export the dbt features model to parquet for the ML layer.

This is the handoff artefact between the dbt transformation layer (source of
truth) and the ML layer (consumer). Run this whenever int_account_transaction_features
changes, then upload the output to Drive.

Usage:
    uv run python scripts/export_features.py
"""

from pathlib import Path

import duckdb

# --- Paths ---
DB_PATH = Path.home() / "projects/fincrime-sentinel/data/processed/fincrime.duckdb"
OUTPUT_DIR = Path.home() / "projects/fincrime-sentinel/data/processed/ml"
OUTPUT_PATH = OUTPUT_DIR / "features.parquet"

# The dbt model to export (schema is main_intermediate in dbt-duckdb)
SOURCE_RELATION = "main_intermediate.int_account_transaction_features"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))
    conn.sql(f"""
        COPY (SELECT * FROM {SOURCE_RELATION})
        TO '{OUTPUT_PATH}' (FORMAT PARQUET)
    """)

    # Verify the export by reading it back in and checking some stats
    df = conn.sql(f"SELECT * FROM read_parquet('{OUTPUT_PATH}')").df()
    conn.close()

    size_mb = OUTPUT_PATH.stat().st_size / 1_048_576
    print(f"Exported to: {OUTPUT_PATH}")
    print(f"File size:   {size_mb:.2f} MB")
    print(f"Rows:        {len(df):,}")
    print(f"Columns:     {len(df.columns)}")
    print(f"Receiver cols present:    {'total_txn_received' in df.columns}")
    print(f"Involvement target present: {'is_laundering_involved' in df.columns}")


if __name__ == "__main__":
    main()
