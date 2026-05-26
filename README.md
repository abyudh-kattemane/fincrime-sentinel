# FinCrime Sentinel

[![CI](https://github.com/abyudhkattemane/fincrime-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/abyudhkattemane/fincrime-sentinel/actions/workflows/ci.yml)

An AUSTRAC-aligned AML transaction monitoring system. Combines rules-based typology detection, ML alert prioritisation, and LLM-assisted investigator narratives on the IBM synthetic AML dataset.

## The problem

Australian banks spend over A$1.5 billion annually on AML compliance. Industry benchmarks put false positive rates at 90–95%.
An investigator opens 100 alerts and roughly 5 are worth pursuing. The 2026 AUSTRAC AML/CTF reforms have raised the bar further. Most AML systems treat this as a volume problem. This project treats it as a design problem.

## The approach

Four layers:

1. **Rules engine** detecting four AUSTRAC typologies: structuring, smurfing, rapid pass-through, velocity anomalies
2. **ML alert scoring** to prioritise high-confidence alerts
3. **LLM case assistant** drafting AUSTRAC-aligned SMR narratives with RAG over real AUSTRAC guidance
4. **Monitoring** for model drift, precision drift, and LLM output quality

Plus an analytics engineering layer (dbt on DuckDB/Motherduck) underneath, and deployment via FastAPI + Streamlit + Power BI.

## Status

This project is being built in public over 10-12 weeks. Progress is tracked in `retrospectives/`.

| Component | Status |
|-----------|--------|
| EDA + rules engine | Done |
| dbt analytics layer | Done |
| ML feature engineering | Done |
| XGBoost scoring + SHAP | In progress |
| LLM case assistant | Not started |
| Deployment (FastAPI + Fly.io) | Not started |
| Monitoring + Power BI | Not started |

## Current results

**Combined rules engine (4 typology detectors):**

| Metric | Value |
|--------|-------|
| Total alerts | 81,749 |
| Precision | 1.3% |
| Recall | 30.5% |

**Fan-out rule (rolling 10-day window):**

| Metric | Value |
|--------|-------|
| Precision | 3.1% |
| Recall | 6.7% |
| Precision@50 | 32% |

The 3.1% global precision matches industry benchmarks. The 32%
precision@50 shows severity ranking is doing real work — the signal
the ML scoring layer (Week 3) will amplify.

---

## Tech stack

- **Data & analytics engineering:** Python, pandas, DuckDB, dbt, Parquet
- **ML:** scikit-learn, XGBoost, SHAP, NetworkX
- **LLM:** Anthropic API, RAG over AUSTRAC PDFs
- **Serving:** FastAPI, Streamlit, Power BI
- **Infrastructure:** uv, ruff, pytest, pre-commit, GitHub Actions, Fly.io

## Data

Synthetic but realistic. See [`data/README.md`](data/README.md).

## Architecture
parquet → rules engine → dbt (staging → intermediate → marts)
→ ML scoring → LLM assistant → Streamlit + FastAPI

## About

Built by [Abyudh Kattemane Annaiah](https://www.linkedin.com/in/abyudh-kattemane-annaiah) — Master of Business Analytics, University of Adelaide, 2025.
