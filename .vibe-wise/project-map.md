# Project Map

## Purpose
SAP AI Learning Agent for LTM SAP BASIS freshers: grounded chat Q&A with citations and clickable diagrams (implemented slice), plus a structured course experience and an admin Course Builder Agent (not built).

## Requirements
- SAP facts grounded in approved sources (TADM ADM328, HANA Admin Guide); mandatory citations; say so when unsupported.
- Interactive diagrams whose elements keep semantic/source IDs (D-08, D-41).
- Course = main attraction: structured modules, diagrams, knowledge checks, AI coach alongside; voice narration required, UX undecided (O-07, O-08).
- Course Builder Agent separate, with admin review/approve/revise loop (D-06, D-10..D-13).
- Retrieval development frozen by user (D-39).

## Components (verified in code, implemented)
- coach/run.py, server.py — FastAPI on 127.0.0.1:8000, serves compiled React (coach/web).
- coach/graph.py — LangGraph: intent → retrieve → generate → validate → commit; InMemorySaver per thread.
- coach/service.py, provider.py, prompts.py — AIcredits openai/gpt-5.6-luna; budget ledger.
- coach/contracts.py — Answer {status, blocks[text, source_ids], diagram{nodes, edges ≤8/≤12}, followups}; source-ID validation.
- coach/retrieval/ — vector + BM25 + structured fusion → NVIDIA nemotron rerank → 10 anchors → 4096-token source expansion.
- coach/ingestion/ — deterministic TADM/HANA PDF profiles → inventory (objects: section, heading, paragraph, figure, caption, table, procedure, objective, assessment, summary, code...) → passages/vectors.
- coach/web/src/main.jsx — chat UI; Diagram renders nodes in a fixed 2-column grid of boxes with straight arrows (no layout engine).
- e01/ — retrieval experiments; not an app dependency.

## Main Flow
learner msg → intent node → Retriever.retrieve() → evidence{id:text,source} → LLM structured Answer → validate citations/diagram → UI (blocks + grouped citations + SVG diagram; click element → selection sent with next message)
Course path: ? (not designed). Course Builder path: ? (not built).

## Data and Trust Boundaries
- Index: coach/data/index (ADM328 PDF pp.41–52 = Unit 3 Maintenance Planner; HANA guide pp.45–61). 1673 objects.
- Keys in project-root .env (AIcredits, NVIDIA). Caches/ledgers in coach/.data.
- Chat memory in-process only.

## Build and Deployment
- cd coach && ../.venv/bin/python run.py ; checks: ../.venv/bin/python check.py
- Frontend: npm ci/build --prefix web (from coach)
- Ingest: ingest.py extract --sources ... --output data/candidates/X ; ingest.py build --dataset ...

## Unknowns
- Course content model storage, display format (O-07), narration timing (O-08).
- Diagram visual grammar/layout approach (current: generic boxes).
- How course and chat connect (D-12 keeps them separate for demo).
