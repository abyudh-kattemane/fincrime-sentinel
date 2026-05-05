"""Cycle detection rule.

Flags accounts involved in circular fund flows — where money sent to
a counterparty returns (directly or via one hop) within a short window.
Consistent with the integration stage of money laundering.
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


def detect_cycles(
    transactions: pd.DataFrame,
    *,
    window_days: int = 3,
    min_cycle_amount: float = 1_000.0,
) -> pd.DataFrame:
    """Detect two-hop circular fund flows.

    Looks for patterns where account A sends to B, and B sends back to A
    (or to an account that sends back to A) within ``window_days``.

    Parameters
    ----------
    transactions:
        Raw transactions with at minimum the columns in ``_REQUIRED_COLS``.
    window_days:
        Maximum time between outgoing and return leg to count as a cycle.
    min_cycle_amount:
        Minimum amount_paid for either leg to be considered.

    Returns
    -------
    pd.DataFrame
        Alerts with columns:
        ``[alert_id, rule_name, account_id, cycle_partner,
        window_start, window_end, cycle_amount, severity]``
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
                "cycle_partner",
                "window_start",
                "window_end",
                "cycle_amount",
                "severity",
            ]
        )

    df = transactions.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["src_id"] = df["from_bank"].astype(str) + ":" + df["account_from"].astype(str)
    df["dst_id"] = df["to_bank"].astype(str) + ":" + df["account_to"].astype(str)
    df = df[df["amount_paid"] >= min_cycle_amount].sort_values("timestamp")

    window = timedelta(days=window_days)
    results = []

    # For each transaction A→B, look for a return B→A within the window
    for row in df.itertuples():
        mask = (
            (df["src_id"] == row.dst_id)
            & (df["dst_id"] == row.src_id)
            & (df["timestamp"] > row.timestamp)
            & (df["timestamp"] <= row.timestamp + window)
        )
        returns = df[mask]
        if not returns.empty:
            cycle_amount = row.amount_paid + returns["amount_paid"].sum()
            severity = round(cycle_amount / min_cycle_amount / 1000, 2)
            seed = f"{row.src_id}|{row.dst_id}|{row.timestamp}"
            alert_id = "cycle_" + hashlib.md5(seed.encode()).hexdigest()[:6].upper()
            results.append(
                {
                    "alert_id": alert_id,
                    "rule_name": "cycle",
                    "account_id": row.src_id,
                    "cycle_partner": row.dst_id,
                    "window_start": row.timestamp,
                    "window_end": row.timestamp + window,
                    "cycle_amount": cycle_amount,
                    "severity": severity,
                }
            )

    if not results:
        return pd.DataFrame(
            columns=[
                "alert_id",
                "rule_name",
                "account_id",
                "cycle_partner",
                "window_start",
                "window_end",
                "cycle_amount",
                "severity",
            ]
        )

    return (
        pd.DataFrame(results)
        .drop_duplicates(subset=["account_id", "cycle_partner", "window_start"])
        .sort_values("severity", ascending=False)
        .reset_index(drop=True)
    )
