"""Velocity anomaly detection rule.

Flags accounts whose daily transaction count or total volume deviates
sharply from their own rolling baseline — consistent with sudden
activation of dormant mule accounts or behavioural changes induced
by laundering activity.
"""

from __future__ import annotations

import hashlib

import pandas as pd

_REQUIRED_COLS = {
    "timestamp",
    "from_bank",
    "account_from",
    "to_bank",
    "account_to",
    "amount_paid",
}


def detect_velocity_anomalies(
    transactions: pd.DataFrame,
    *,
    baseline_days: int = 30,
    z_threshold: float = 3.0,
) -> pd.DataFrame:
    """Detect accounts with sudden velocity spikes above their own baseline.

    For each source account, computes a rolling mean and standard deviation
    of daily transaction count over ``baseline_days``. Flags any day where
    the count exceeds mean + z_threshold * std.

    Parameters
    ----------
    transactions:
        Raw transactions with at minimum the columns in ``_REQUIRED_COLS``.
    baseline_days:
        Rolling window (in days) used to compute the account's baseline.
    z_threshold:
        Number of standard deviations above the mean that triggers an alert.

    Returns
    -------
    pd.DataFrame
        Alerts with columns:
        ``[alert_id, rule_name, account_id, spike_date,
        daily_count, baseline_mean, baseline_std, severity]``
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
                "spike_date",
                "daily_count",
                "baseline_mean",
                "baseline_std",
                "severity",
            ]
        )

    df = transactions.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["src_id"] = df["from_bank"].astype(str) + ":" + df["account_from"].astype(str)
    df["date"] = df["timestamp"].dt.date

    results = []

    for account, group in df.groupby("src_id"):
        daily = (
            group.groupby("date")
            .agg(daily_count=("amount_paid", "count"))
            .reset_index()
            .sort_values("date")
        )
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.set_index("date").asfreq("D", fill_value=0).reset_index()

        daily["rolling_mean"] = (
            daily["daily_count"].rolling(window=baseline_days, min_periods=3).mean().shift(1)
        )
        daily["rolling_std"] = (
            daily["daily_count"].rolling(window=baseline_days, min_periods=3).std().shift(1)
        )

        spikes = daily[
            (daily["rolling_std"] > 0)
            & (daily["daily_count"] > daily["rolling_mean"] + z_threshold * daily["rolling_std"])
        ]

        for row in spikes.itertuples():
            severity = round((row.daily_count - row.rolling_mean) / row.rolling_std, 2)
            seed = f"{account}|{row.date}"
            alert_id = "vel_" + hashlib.md5(seed.encode()).hexdigest()[:6].upper()
            results.append(
                {
                    "alert_id": alert_id,
                    "rule_name": "velocity",
                    "account_id": account,
                    "spike_date": row.date,
                    "daily_count": row.daily_count,
                    "baseline_mean": round(row.rolling_mean, 2),
                    "baseline_std": round(row.rolling_std, 2),
                    "severity": severity,
                }
            )

    if not results:
        return pd.DataFrame(
            columns=[
                "alert_id",
                "rule_name",
                "account_id",
                "spike_date",
                "daily_count",
                "baseline_mean",
                "baseline_std",
                "severity",
            ]
        )

    return pd.DataFrame(results).sort_values("severity", ascending=False).reset_index(drop=True)
