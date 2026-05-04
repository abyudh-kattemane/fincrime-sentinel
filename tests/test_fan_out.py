"""Unit tests for the fan-out detection rule."""

from __future__ import annotations

import pandas as pd
import pytest

from src.rules.fan_out import detect_fan_out


def _build_transactions(rows: list[dict]) -> pd.DataFrame:
    """Construct a transactions DataFrame from a list of dicts.

    Helper for compact, readable test fixtures.
    """
    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "from_bank",
                "account_from",
                "to_bank",
                "account_to",
                "amount_paid",
            ]
        )
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# ── Happy path tests ─────────────────────────────────────────────────


def test_detects_obvious_fan_out():
    """An account hitting 10 distinct destinations in 2 days is flagged."""
    rows = [
        {
            "timestamp": "2022-09-01 10:00",
            "from_bank": 70,
            "account_from": "A",
            "to_bank": 70,
            "account_to": f"D{i}",
            "amount_paid": 6000,
        }
        for i in range(10)
    ]
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, min_destinations=8, min_total_amount=50_000)

    assert len(alerts) == 1
    assert alerts.iloc[0]["account_id"] == "70:A"
    assert alerts.iloc[0]["destination_count"] == 10
    assert alerts.iloc[0]["total_amount"] == 60_000
    assert alerts.iloc[0]["rule_name"] == "fan_out"


def test_does_not_flag_legitimate_account():
    """Account with only 3 destinations does not trigger an alert."""
    rows = [
        {
            "timestamp": "2022-09-01 10:00",
            "from_bank": 70,
            "account_from": "A",
            "to_bank": 70,
            "account_to": f"D{i}",
            "amount_paid": 100_000,
        }
        for i in range(3)
    ]
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, min_destinations=8)

    assert len(alerts) == 0


def test_below_amount_threshold_not_flagged():
    """Many destinations but tiny amounts — should not flag."""
    rows = [
        {
            "timestamp": "2022-09-01 10:00",
            "from_bank": 70,
            "account_from": "A",
            "to_bank": 70,
            "account_to": f"D{i}",
            "amount_paid": 100,
        }  # total = 1000, below 50K threshold
        for i in range(10)
    ]
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, min_destinations=8, min_total_amount=50_000)

    assert len(alerts) == 0


def test_outside_window_not_aggregated():
    """Destinations spread over more than window_days are not summed."""
    rows = []
    # 6 destinations on day 1
    for i in range(6):
        rows.append(
            {
                "timestamp": "2022-09-01 10:00",
                "from_bank": 70,
                "account_from": "A",
                "to_bank": 70,
                "account_to": f"D{i}",
                "amount_paid": 10_000,
            }
        )
    # 6 more destinations on day 30 (way outside any reasonable window)
    for i in range(6, 12):
        rows.append(
            {
                "timestamp": "2022-10-01 10:00",
                "from_bank": 70,
                "account_from": "A",
                "to_bank": 70,
                "account_to": f"D{i}",
                "amount_paid": 10_000,
            }
        )
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, window_days=5, min_destinations=8)

    assert len(alerts) == 0


def test_one_alert_per_account():
    """Account that sustains fan-out for many days only generates one alert."""
    rows = []
    for day in range(10):
        for dest in range(10):
            rows.append(
                {
                    "timestamp": f"2022-09-{day + 1:02d} 10:00",
                    "from_bank": 70,
                    "account_from": "A",
                    "to_bank": 70,
                    "account_to": f"D{day}_{dest}",
                    "amount_paid": 6_000,
                }
            )
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, window_days=5, min_destinations=8)

    assert len(alerts) == 1


# ── Edge cases ────────────────────────────────────────────────────────


def test_empty_input_returns_empty_alerts():
    """Empty DataFrame returns empty alerts with correct schema."""
    df = _build_transactions([])
    alerts = detect_fan_out(df)

    assert len(alerts) == 0
    assert "alert_id" in alerts.columns
    assert "rule_name" in alerts.columns


def test_missing_columns_raises():
    """DataFrame without required columns raises ValueError."""
    df = pd.DataFrame({"foo": [1, 2, 3]})

    with pytest.raises(ValueError, match="missing required columns"):
        detect_fan_out(df)


def test_distinct_accounts_handled_separately():
    """Two different source accounts each fanning out — each gets its own alert."""
    rows = []
    for src in ["A", "B"]:
        for dest in range(10):
            rows.append(
                {
                    "timestamp": "2022-09-01 10:00",
                    "from_bank": 70,
                    "account_from": src,
                    "to_bank": 70,
                    "account_to": f"{src}_D{dest}",
                    "amount_paid": 6_000,
                }
            )
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, min_destinations=8)

    assert len(alerts) == 2
    assert set(alerts["account_id"]) == {"70:A", "70:B"}


def test_severity_calculation():
    """Severity should be destination_count / min_destinations, rounded."""
    rows = [
        {
            "timestamp": "2022-09-01 10:00",
            "from_bank": 70,
            "account_from": "A",
            "to_bank": 70,
            "account_to": f"D{i}",
            "amount_paid": 6_000,
        }
        for i in range(16)  # 16 / 8 = 2.0
    ]
    df = _build_transactions(rows)

    alerts = detect_fan_out(df, min_destinations=8)

    assert alerts.iloc[0]["severity"] == 2.0
