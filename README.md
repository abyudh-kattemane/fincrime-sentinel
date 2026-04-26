# FinCrime Sentinel

[![CI](https://github.com/abyudhkattemane/fincrime-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/abyudhkattemane/fincrime-sentinel/actions/workflows/ci.yml)

An AUSTRAC-aligned AML transaction monitoring system. Combines rules-based typology detection, ML alert prioritisation, and LLM-assisted investigator narratives on the IBM synthetic AML dataset.

## The problem

Australian banks spend over A$1.5 billion annually on AML compliance. Industry false-positive rates on transaction monitoring run 90–95%, meaning investigators review ten alerts to find one real laundering case. The 2026 AUSTRAC AML/CTF reforms have raised the bar further. Most AML systems treat this as a volume problem. This project treats it as a design problem.

## The approach

Four layers:

1. **Rules engine** detecting four AUSTRAC typologies: structuring, smurfing, rapid pass-through, velocity anomalies
2. **ML alert scoring** to prioritise high-confidence alerts
3. **LLM case assistant** drafting AUSTRAC-aligned SMR narratives with RAG over real AUSTRAC guidance
4. **Monitoring** for model drift, precision drift, and LLM output quality

Plus an analytics engineering layer (dbt on DuckDB/Motherduck) underneath, and deployment via FastAPI + Streamlit + Power BI.

## Status

This project is being built in public over 8 weeks. Progress is tracked in `retrospectives/`.

**Week 1 (current):** Repo foundation, EDA, rules engine scaffolding.

## Tech stack

- **Data & analytics engineering:** Python, pandas, DuckDB, dbt, Parquet
- **ML:** scikit-learn, XGBoost, SHAP, NetworkX
- **LLM:** Anthropic API, RAG over AUSTRAC PDFs
- **Serving:** FastAPI, Streamlit, Power BI
- **Infrastructure:** uv, ruff, pytest, pre-commit, GitHub Actions, Fly.io

## Data

Synthetic but realistic. See [`data/README.md`](data/README.md).

## Writing

Weekly posts on Medium:
- Week 1: *Why Australian AML false positives are a design problem, not a volume problem* (coming Sunday)

## About

Built by [Abyudh Kattemane Annaiah](https://www.linkedin.com/in/abyudh-kattemane-annaiah) — Master of Business Analytics, University of Adelaide, 2025.
