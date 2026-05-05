"""Rules engine — consolidated alert generation.

Runs all four typology detectors and merges output into a single
alerts DataFrame with a standardised schema.
"""

from __future__ import annotations

import pandas as pd

from src.rules.cycle import detect_cycles
from src.rules.fan_in import detect_fan_in
from src.rules.fan_out import detect_fan_out
from src.rules.velocity import detect_velocity_anomalies

_STANDARD_COLS = ["alert_id", "rule_name", "account_id", "severity"]


def run_all_rules(
    transactions: pd.DataFrame,
    *,
    fan_out_kwargs: dict | None = None,
    fan_in_kwargs: dict | None = None,
    cycle_kwargs: dict | None = None,
    velocity_kwargs: dict | None = None,
) -> pd.DataFrame:
    """Run all four typology detection rules and consolidate alerts.

    Parameters
    ----------
    transactions:
        Raw transactions DataFrame.
    fan_out_kwargs / fan_in_kwargs / cycle_kwargs / velocity_kwargs:
        Optional dicts of keyword arguments forwarded to each detector.
        Use these to override default thresholds without changing function
        signatures.

    Returns
    -------
    pd.DataFrame
        Combined alerts with at minimum
        ``[alert_id, rule_name, account_id, severity]``.
        Rule-specific columns are preserved but non-common columns will
        be NaN for rows from other rules.
    """
    fan_out_kwargs = fan_out_kwargs or {}
    fan_in_kwargs = fan_in_kwargs or {}
    cycle_kwargs = cycle_kwargs or {}
    velocity_kwargs = velocity_kwargs or {}

    results = [
        detect_fan_out(transactions, **fan_out_kwargs),
        detect_fan_in(transactions, **fan_in_kwargs),
        detect_cycles(transactions, **cycle_kwargs),
        detect_velocity_anomalies(transactions, **velocity_kwargs),
    ]

    combined = pd.concat(results, ignore_index=True)
    return combined.sort_values("severity", ascending=False).reset_index(drop=True)
