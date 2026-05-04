"""Fan-out laundering pattern detection.

A fan-out pattern occurs when a single source account distributes
funds to many destination accounts within a short time window. This
behaviour often indicates the layering stage of money laundering —
splitting placed funds across multiple accounts to obscure their
origin.
"""

from __future__ import annotations

import pandas as pd


def detect_fan_out(
    transactions: pd.DataFrame,
    *,
    window_days: int = 5,
    min_destinations: int = 8,
    min_total_amount: float = 50_000,
) -> pd.DataFrame:
    """Flag accounts exhibiting fan-out distribution patterns.

    For each source account, examines all rolling windows of size
    ``window_days``. If a window contains transactions to at least
    ``min_destinations`` distinct destination accounts and the total
    transferred exceeds ``min_total_amount``, the account is flagged.

    Parameters
    ----------
    transactions
        Transaction-level DataFrame with columns: ``timestamp``,
        ``from_bank``, ``account_from``, ``to_bank``, ``account_to``,
        ``amount_paid``. Sorted order is not required.
    window_days
        Width of the rolling window in days.
    min_destinations
        Minimum number of distinct destinations within a window
        required to trigger an alert.
    min_total_amount
        Minimum total amount transferred within the window.

    Returns
    -------
    DataFrame
        Alerts with columns: ``alert_id``, ``rule_name``,
        ``account_id``, ``window_start``, ``window_end``,
        ``destination_count``, ``total_amount``, ``severity``.
    """

    required_cols = {
        "timestamp",
        "from_bank",
        "account_from",
        "to_bank",
        "account_to",
        "amount_paid",
    }
    missing = required_cols - set(transactions.columns)
    if missing:
        raise ValueError(f"transactions missing required columns: {missing}")

    if len(transactions) == 0:
        return _empty_alerts()

    # ── Build a per-source-account view, sorted by time ──────────────
    df = transactions[
        ["timestamp", "from_bank", "account_from", "account_to", "amount_paid"]
    ].copy()
    df["source_id"] = df["from_bank"].astype(str) + ":" + df["account_from"].astype(str)
    df = df.sort_values(["source_id", "timestamp"]).reset_index(drop=True)

    # ── Rolling window aggregation per source account ────────────────
    window = pd.Timedelta(days=window_days)
    alerts = []

    for source_id, group in df.groupby("source_id", sort=False):
        # For each transaction, look at the prior `window` of activity
        for end_ts in group["timestamp"]:
            start_ts = end_ts - window
            window_slice = group[(group["timestamp"] >= start_ts) & (group["timestamp"] <= end_ts)]

            destination_count = window_slice["account_to"].nunique()
            total_amount = window_slice["amount_paid"].sum()

            if destination_count >= min_destinations and total_amount >= min_total_amount:
                alerts.append(
                    {
                        "account_id": source_id,
                        "window_start": start_ts,
                        "window_end": end_ts,
                        "destination_count": destination_count,
                        "total_amount": total_amount,
                    }
                )
                break  # one alert per account per run

    if not alerts:
        return _empty_alerts()

    # ── Build the output DataFrame ───────────────────────────────────
    result = pd.DataFrame(alerts)
    result["rule_name"] = "fan_out"
    result["severity"] = (result["destination_count"] / min_destinations).round(2)
    result["alert_id"] = [f"fan_out_{i:06d}" for i in range(len(result))]
    return result[
        [
            "alert_id",
            "rule_name",
            "account_id",
            "window_start",
            "window_end",
            "destination_count",
            "total_amount",
            "severity",
        ]
    ]


def _empty_alerts() -> pd.DataFrame:
    """Return an empty alerts DataFrame with the canonical schema."""
    return pd.DataFrame(
        columns=[
            "alert_id",
            "rule_name",
            "account_id",
            "window_start",
            "window_end",
            "destination_count",
            "total_amount",
            "severity",
        ]
    )
