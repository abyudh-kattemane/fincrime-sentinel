## Day 14 — Tuesday 02 June (dbt backfill)

What I did:
– Built int_fan_in/cycle/velocity alert models, refactored fct_alerts to UNION ALL four rules
– Built dim_accounts as complete entity registry (senders + receivers)
– Tuned cycle and velocity thresholds across multiple passes

What I learned:
– UNION ALL over UNION for performance and never-silently-drop safety
– Dimensions must be complete entity registries — the relationships test caught 277 receiver-only accounts missing from dim_accounts
– Threshold tuning is iterative configuration, not fixed law
– Rolling-window counts (Python) produce account-window rows; full-window (dbt) produces account rows — explains count differences

What went wrong:
– First dim_accounts only had senders, broke the relationships test on fan_in alerts
– Threshold tuning overcorrected twice before landing in operational range

## Day 15 — Wednesday 10 June (LLM case assistant — RAG foundation)

What I did:
– Set up Anthropic API access via Colab secrets; verified with a test call and token-cost printout
– Identified three AUSTRAC source documents (typologies indicators, real estate brief, digital currencies guide)
– Discovered the "PDFs" were ZIP-wrapped page images, not real PDFs — re-sourced two as real PDFs, extracted the third from embedded OCR text
– Built the RAG pipeline: pypdf extraction, 800-char chunks with 100-char overlap, all-MiniLM-L6-v2 embeddings, ChromaDB vector store with source metadata
– Verified retrieval: a multi-currency/high-destination query returned relevant structuring, u-turn, and wallet-clustering guidance from two of the three docs

What I learned:
– RAG grounds an LLM in domain source material rather than its training data — essential for AML typology language the model wasn't trained on
– Chunk size is a precision/context trade-off; overlap prevents information loss at boundaries
– Embedding similarity is geometric proximity in vector space — captures meaning, not keywords. Cosine similarity on 384-dim vectors
– Local embeddings (sentence-transformers) over an API: no cost, no dependency, reproducible — right call for a static corpus, wrong call for live high-volume queries
– Metadata on each chunk is what makes citations possible — retrieval without source attribution produces unverifiable claims
