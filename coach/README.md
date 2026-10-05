# SAP Learning Coach

The chatbot owns its retrieval and ingestion code. It does not import or read `e01`, the parent `output`, `docs`, or `tmp` directories. The Python virtual environment and API credentials live at the project root, as requested.

## Reading the code for the first time

Each main Python module now starts with a `READER GUIDE`: its responsibility, input/output flow, and boundaries. Inline comments explain decisions and include examples where the logic is less obvious.

Follow one learner question through these files:

1. **`server.py` → `graph.py`**: HTTP request, conversation lookup, intent routing and saving a completed turn.
2. **`service.py` → `prompts.py` → `contracts.py`**: what each model call receives, what it should return, and what the app accepts or omits.
3. **`retrieval/retriever.py` → `hybrid.py` → `vector.py` / `reranker.py`**: candidate search, ranking and assembling cited evidence. Start with the retriever before the scoring mathematics.
4. **`provider.py`**: exact-request caching, reservations, network submission and errors. Read this when tracing cost or provider failures.
5. **`web/src/main.jsx`**: how the returned turn becomes chat text, page citations and a selectable diagram.

Then follow the separate data preparation path: `ingest.py` → `ingestion/pipeline.py` → `extractor.py` / `procedures.py` → `chunking.py` → `retrieval/index_store.py`. Ingestion builds files; chat retrieval reads them.

Four terms help connect the layers:

| Term | Meaning |
|---|---|
| Canonical object | A source content unit with a stable ID and PDF location. |
| Window | A token-limited slice used for embedding; several can belong to one object. |
| Anchor | A ranked object selected as a starting point for evidence assembly. |
| Evidence | Original source text sent to the answer model, with IDs used for citations. |

For concrete failure examples, read the fixture tests in `test_coach.py`. Run `check.py` for offline checks; `smoke.py` and `quality_check.py` can make paid API calls.

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

## First-time setup, in order

Run these commands from a terminal. Git LFS must be installed on your computer before cloning; `git lfs install` configures it for your account:

```sh
git lfs install
git clone https://github.com/nxvnth/SAP_COACH.git
cd SAP_COACH
python3.11 -m venv .venv
.venv/bin/python -m pip install -r coach/runtime-lock.txt
```

Next, obtain authorized copies of the two PDFs named above and put them in `coach/data/documents/`. The filenames must match `ingestion/sources.example.json` exactly. Copy `.env.example` to `.env` at the project root and replace the placeholders with your API keys; the keys are needed to run chat, but not to extract PDFs or build the local index.

Then, from the repository root, run the extraction and index-building commands in order:

```sh
cd coach
../.venv/bin/python ingest.py extract \
  --sources ingestion/sources.example.json \
  --output data/candidates/local
../.venv/bin/python ingest.py build --dataset data/candidates/local
```

Finally, still from `coach`, start the app using the index you just built:

```sh
SAP_COACH_INDEX="$PWD/data/candidates/local" ../.venv/bin/python run.py
```

Open http://127.0.0.1:8000. Index creation uses the included local embedding model and does not require a model-hub download. Keep the generated `data/candidates/local` directory on your machine; it is ignored by Git and must be rebuilt when setting up another checkout.

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
