"""Fan-in (smurfing aggregation) detection rule.

Flags destination accounts that receive funds from an unusually large
number of distinct source accounts within a rolling time window —
consistent with aggregation behaviour in the placement or integration
stage of money laundering.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta

import pandas as pd

_REQUIRED_COLS = {
    "timestamp",
    "from_bank",
    "account_from",
    "to_bank",
    "account_to",
    "amount_paid",
}


def detect_fan_in(
    transactions: pd.DataFrame,
    *,
    window_days: int = 10,
    min_sources: int = 8,
) -> pd.DataFrame:
    """Detect fan-in aggregation patterns in a transactions DataFrame.

    Parameters
    ----------
    transactions:
        Raw transactions with at minimum the columns in ``_REQUIRED_COLS``.
    window_days:
        Rolling window length in days over which to count distinct sources.
    min_sources:
        Minimum number of distinct source accounts required to trigger an alert.

    Returns
    -------
    pd.DataFrame
        Alerts with columns:
        ``[alert_id, rule_name, account_id, window_start, window_end,
        source_count, total_amount, severity]``

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({...})  # transactions
    >>> alerts = detect_fan_in(df, window_days=10, min_sources=8)
    """
    missing = _REQUIRED_COLS - set(transactions.columns)
    if missing:
        raise ValueError(f"transactions missing required columns: {missing}")

    if transactions.empty:
        return pd.DataFrame(
            columns=[
                "alert_id",
                "rule_name",
                "account_id",
                "window_start",
                "window_end",
                "source_count",
                "total_amount",
                "severity",
            ]
        )

    df = transactions.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    dest_id = df["to_bank"].astype(str) + ":" + df["account_to"].astype(str)
    src_id = df["from_bank"].astype(str) + ":" + df["account_from"].astype(str)
    df["dest_id"] = dest_id
    df["src_id"] = src_id

    window = timedelta(days=window_days)
    results = []

    for account, group in df.groupby("dest_id"):
        group = group.sort_values("timestamp")
        for row in group.itertuples():
            mask = (group["timestamp"] >= row.timestamp - window) & (
                group["timestamp"] <= row.timestamp
            )
            window_rows = group[mask]
            source_count = window_rows["src_id"].nunique()
            if source_count >= min_sources:
                total_amount = window_rows["amount_paid"].sum()
                severity = round(source_count / min_sources, 2)
                seed = f"{account}|{row.timestamp}|{window_days}"
                alert_id = "fan_in_" + hashlib.md5(seed.encode()).hexdigest()[:6].upper()
                results.append(
                    {
                        "alert_id": alert_id,
                        "rule_name": "fan_in",
                        "account_id": account,
                        "window_start": row.timestamp - window,
                        "window_end": row.timestamp,
                        "source_count": source_count,
                        "total_amount": total_amount,
                        "severity": severity,
                    }
                )

    if not results:
        return pd.DataFrame(
            columns=[
                "alert_id",
                "rule_name",
                "account_id",
                "window_start",
                "window_end",
                "source_count",
                "total_amount",
                "severity",
            ]
        )

    return (
        pd.DataFrame(results)
        .drop_duplicates(subset=["account_id", "window_start"])
        .sort_values("severity", ascending=False)
        .reset_index(drop=True)
    )
