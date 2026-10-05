# SAP Learning Coach

The chatbot owns its retrieval and ingestion code. It does not import or read `e01`, the parent `output`, `docs`, or `tmp` directories. The Python virtual environment and API credentials live at the project root, as requested.

## Run from coach

```sh
cd coach
../.venv/bin/python run.py
```

Open http://127.0.0.1:8000. The compiled React frontend is included. The server uses one worker and binds to localhost. Restarting clears LangGraph's in-memory conversations.

For a new checkout, first run from the project root:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r coach/runtime-lock.txt
```

Set `AIAPIKEY` and `NVIDIA_API_KEY` in the **project root `.env`** using `.env.example`. Environment variables also work. Credentials are not read from `coach/.env`. Never distribute credentials or `.data` caches. `requirements.txt` lists direct dependencies; `runtime-lock.txt` records the verified full environment.

To rebuild the frontend, run `npm ci --prefix web` and `npm run build --prefix web` from `coach`.

## Layout

```text
SAP_COACH/
├── .venv/                     Python environment
├── .env                       API keys (ignored)
├── e01/                       Experiments only; not an app dependency
└── coach/
    ├── run.py                 Chatbot entry point
    ├── ingest.py              Offline ingestion entry point
    ├── graph.py               Intent → retrieval → teaching → validation
    ├── service.py             Model calls and retrieval interface
    ├── provider.py            AIcredits client and budget ledger
    ├── retrieval/
    │   ├── retriever.py       Public retrieval entry point
    │   ├── hybrid.py          Vector/BM25/structured fusion and source expansion
    │   ├── vector.py          Embedding model, evidence units and vector search
    │   ├── reranker.py        NVIDIA API, cache and attempt ledger
    │   ├── index_store.py     Versioned index integrity contract
    │   └── embedding_model.json
    ├── ingestion/
    │   ├── extractor.py       TADM/HANA PDF extraction profiles
    │   ├── procedures.py      Numbered procedure normalization
    │   ├── chunking.py        Token windows with source spans
    │   ├── pipeline.py        Validation and candidate index building
    │   └── sources.example.json
    ├── data/
    │   ├── documents/        Local source PDFs (not included in Git)
    │   ├── models/           Local BGE embedding model (weights via Git LFS)
    │   └── index/            Locally built inventory, passages, vectors and manifests
    ├── web/                  React source and build
    └── .data/                Chat API/reranking caches and ledgers (ignored)
```

The historical runtime snapshot was moved to the ignored project `tmp/coach_before_packages` for traceability. The app never reads it. Existing experiments and their benchmark results remain unchanged.

## Set up the local document data

Source PDFs and generated indexes are not included in this repository. Obtain authorized copies of the exact editions configured in `ingestion/sources.example.json` and place them here, using these filenames:

```text
coach/data/documents/ADM328_EN_Col23.pdf
coach/data/documents/SAP_HANA_Administration_Guide_en.pdf
```

The PDFs, extracted text, and generated indexes are intentionally excluded from Git. Do not commit or redistribute them unless you have permission. The embedding model weights are stored with Git LFS; install Git LFS before cloning so the weights are downloaded.

## Retrieval replacement boundary

`service.py` imports `Retriever` from `coach.retrieval`. It can also receive an alternative retriever through `TeachingService(retriever=...)`. Keep this method when promoting an experiment:

```python
retrieve(message: str, history: list, selection: dict | None) -> dict
```

The message is already resolved by the intent node. Do not prepend old history again. Return:

- `evidence`: mapping of canonical source ID to `{id, text, source}`; source locations include document ID and PDF page.
- `retrieval_tokens`: measured retrieved context size.
- `selected_source_ids`: extra grounding references from an explicitly relevant diagram selection.
- `query` and `selected_anchor_ids`: retrieval trace for debugging.

Internal ranking and storage can change behind this interface. If changing embeddings or chunking, rebuild the index too. The version-1 index manifest records hashes of inventory, source manifest, passages and vectors, plus embedding model identity. It does not depend on benchmark questions, experimental Python files or their hashes.

Current behavior: vector/BM25/structured fused candidates → NVIDIA `llama-nemotron-rerank-vl-1b-v2` → ten anchors → source expansion within 4096 tokens. Extra selected-element references are disclosed separately. Graph/facet experimental variants are not enabled. The package refactor does not change this ranking policy.

## Ingest data separately

The existing PDF profiles are deterministic and edition-specific. They preserve text, table rows, procedure steps and figure crops/captions. They do not interpret image contents or build an LLM knowledge graph. Review extraction issues before using a new index; passing structural validation is not a semantic quality guarantee. The example source file lists the required PDF filenames, profiles, and inclusive page ranges.

From `coach`, create a candidate dataset:

```sh
../.venv/bin/python ingest.py extract \
  --sources ingestion/sources.example.json \
  --output data/candidates/example
```

The source JSON lists document `key`, PDF `file`, `profile` (`tadm` or `hana`), and inclusive PDF page `start`/`end`. PDFs default to `data/documents`; `--documents` accepts another input directory. For the chatbot to serve citations, source files must also exist under `data/documents` with the manifest filenames.

Inspect the candidate's `review.html`, `issues.json` and `validation.json`, then build:

```sh
../.venv/bin/python ingest.py build --dataset data/candidates/example
```

Building refuses extraction errors and never overwrites the active or an already built index. Extraction requires a new output directory. Candidate data is local and ignored by Git. This is a complete candidate dataset, not an automatic append to the current chapters: include all desired ranges for a replacement corpus.

Test a candidate without replacing the default dataset:

```sh
SAP_COACH_INDEX="$PWD/data/candidates/example" ../.venv/bin/python run.py
```

Because the active index is built locally and is not included in Git, set `SAP_COACH_INDEX` to the built candidate directory when starting the app. Stop the old server before starting another on the same port. Existing API caches and budgets remain in `.data`; changing an index does not reset them.

## Model, memory and validation

AIcredits `openai/gpt-5.6-luna` generates answers and resolves contextual queries. New standalone topics omit previous history and stale selections; follow-ups resolve recent references. An ambiguous query asks for clarification before retrieval. Initial messages without history/selection skip the intent model call.

LangGraph uses `InMemorySaver`; successful turns are committed per thread. Failed turns are excluded. Context is bounded to 12 messages / 16,000 characters, without automatic long-term summarization. The historical SQLite store remains an unused archive.

Partial answers explain supported facts and specific gaps. Follow-up buttons use learner-worded requests; clarification questions are separate. Citations group excerpts by document/PDF page. Invalid text citations reject the answer; a broken optional diagram is omitted without losing valid text. Citation-ID validation does not establish factual entailment.

AIcredits retains its $0.50 reservation / 20-call cap in `config.json`. NVIDIA has a separate 200-attempt ledger; AIcredits reservations do not cover NVIDIA charges. Neither client automatically retries uncertain attempts.

## Check

From `coach`:

```sh
../.venv/bin/python check.py
../.venv/bin/python verify_standalone.py  # optional isolated-copy check
```

Verified after package migration: offline regressions, identical anchors/evidence on three cached queries, PDF extraction → index build → search, and isolated app loading without the experiment folder. No new paid calls or browser visual QA are needed for this packaging change.
