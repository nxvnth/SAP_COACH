# SAP AI Learning Agent — Design Decision Log

Sep 24, 2026 · @navaneeth

## How to use this log

This log records every design and technical decision for the SAP AI Learning Agent, with the failure each one solves. It supplements handoff.md; where they conflict, this log is newer.

Status words used below: **Decided** (agreed, build to it), **Demo-scoped** (true for the demo only, revisit after), **Hypothesis** (to be proven by an experiment), **Open** (not decided, do not invent), **Needs confirmation** (depends on someone else).

## Decisions made

| ID | Area | Decision | Status | Failure it solves |
| --- | --- | --- | --- | --- |
| D-01 | Ingestion | One ingestion framework with per-document-type parser profiles (TADM, SAP Help / HANA guide) feeding a shared canonical model. Shown as one box with profile labels in the main deck. | Decided | A single generic parser flattens TADM pedagogy and HANA guide hierarchy into chunks, losing citation locations and structure. |
| D-02 | Ingestion | Assessments are an optional object type in the canonical model. Only TADM profiles produce them. | Decided | Forcing every source to fit TADM structure; the HANA guide has no assessments. |
| D-03 | Retrieval | First implementation is parallel fan-out: BM25, vector and structured lookup run on every query. The Query Router is removed from the main diagram. | Decided | Presenting routing (unproven) as the design; router misroutes silently drop the right channel. |
| D-04 | Retrieval | Results from all channels merge by canonical ID before enrichment. | Decided | The same object returned by two channels would appear twice and waste context. |
| D-05 | Retrieval | Candidates are judged on relevance to the query, not on how densely they link to other candidates. | Decided | Hub concepts (for example SAP HANA database) link to everything and would crowd out the specific answer. |
| D-06 | Agents | Two agents: Main AI Agent (learner chat) and Course Builder Agent (admin). Different instructions, same core tools (SAP Data Tool, Interactive Diagram Tool); Course Builder may get extra authoring tools. | Decided | One agent serving two users with different goals and outputs. |
| D-07 | Diagrams | The Interactive Diagram Tool does no retrieval. The agent calls it only after it has grounded context and decides a visual helps. Diagram syntax rules live in a skill. | Decided | Duplicated retrieval inside a rendering tool; diagrams drawn from ungrounded content. |
| D-08 | Diagrams | Every diagram node or edge that comes from source content carries the canonical ID of that object. Explanatory-only nodes are marked as not source-grounded. | Decided | Learner selection cannot be resolved back to SAP content later; generated relationships mistaken for source facts. |
| D-09 | SAP Notes | SAP Notes / KBAs are retrieved on demand through a generic SAP Notes Retrieval Tool, not ingested. Demo uses an existing MCP server with the user's own account. | Demo-scoped | Building ingestion for a large, fast-changing, situational corpus. |
| D-10 | Course | Course drafts are stored; no version history for the demo. | Demo-scoped | Versioning cost before any reviewed module exists. |
| D-11 | Course | Admin/Course Builder history is stored separately from learner conversation history. | Decided | Admin drafts and learner chats have different access and retention needs. |
| D-12 | Course | Course and chatbot are separate in the demo. Course sections and diagram elements still get stable IDs at generation time. | Demo-scoped | Later course-context chat would require regenerating every module to add IDs. |
| D-13 | Course | The module content model (objectives, sections, diagrams, quiz, narration script, citations) is independent of display format. A renderer decides how it is shown. | Decided | Locking the content model to one format before the format is chosen. |
| D-14 | Diagrams (deck) | Separate diagrams: component architecture, ingestion, course builder flow, and one learner interaction/journey diagram. | Decided | One diagram trying to show components and user interaction at once becomes unreadable. |

### Added 24 Sep 2026 (director presentation)

| ID | Area | Decision | Status | Failure it solves |
| --- | --- | --- | --- | --- |
| D-15 | Stack | Build phase uses Python and Node.js on open-source components; no SAP AI Core or other SAP products. Migrate to SAP-native services only after the build is proven and showcased. | Decided | Platform dependencies and approvals slowing the proof of the design. |
| D-16 | Stack | Proposed build components: React / Next.js UI; Python + FastAPI backend with native LLM tool calling; PyMuPDF and Docling parsers; ChromaDB, rank-bm25, open-source reranker; SQLite (graph) and PostgreSQL (history, courses); MCP connectors for SAP Notes and draw.io. | Proposed | Needs user confirmation per component; LLM model and TTS engine still open. |
| D-17 | Stack | Indicative SAP-native mapping: SAPUI5/Fiori, SAP BTP runtime, SAP AI Core Generative AI Hub, SAP HANA Cloud (vector engine, full-text search, data). | Proposed | Shows the path to an SAP-native solution without committing early. |
| D-18 | Presentation | Audience: senior principal director with manager, 10 to 15 minutes. Goal: build confidence that the work is under way and will continue. Evaluation detail stays in the appendix; unsupported-question handling is stated on the journey and query slides. | Decided | Losing a non-specialist audience in retrieval metrics. |
| D-19 | Presentation | Voice framed as part of the content model; delivery format chosen by testing with trainees. | Decided | Overcommitting to a narration UX before testing. |

## Scoped out or deferred

| Item | Why deferred | Revisit when |
| --- | --- | --- |
| Chat inside the course (select text, section or diagram element and ask) | Demo keeps course and chat separate | After the demo; D-12 keeps the IDs ready |
| Course version history | Drafts are enough for one reviewed module | More than one admin, or modules edited after publishing |
| Vision processing of figures | Cost and uncertainty; figure-level approach in E-01 first | E-01 shows validation queries fail because figure content is missing |
| SAP System Integration Tool build | Training system access needs approvals | Manager confirms system access; show as planned in the deck meanwhile |
| Query router (R2) | No evidence yet that fan-out is too noisy or slow | E-01 shows fan-out noise, latency or ranking problems |

## Open decisions

| ID | Question | Options on the table | Resolved by |
| --- | --- | --- | --- |
| O-01 | What gets indexed in Vector DB and BM25? | Content objects only; nodes only; both with shared ID | E-01 |
| O-02 | How are channel results fused? | Reciprocal Rank Fusion baseline; weighted fusion; exact structured matches pinned to the top | E-01 |
| O-03 | What does the reranker score: the anchor alone, or anchor plus enrichment? | Anchor only (cheaper, sharper); anchor with enrichment (more context, noisier) | E-01 |
| O-04 | When a child and its parent are both retrieved, what happens? | Keep child as candidate, attach parent as context; keep both | E-01 |
| O-05 | How is figure content represented? | Figure object with caption, nearby text and page reference, image shown to learner; plus offline vision descriptions reviewed by a human | E-01 (count queries that need figures) |
| O-06 | Who decides the retrieved context is insufficient to answer? | Agent judges alone; Context Builder returns a coverage/confidence signal from reranker scores | E-01 with out-of-scope queries |
| O-07 | Course display format | Slides with voiceover; textbook; documentation; guided walkthrough; scenario-based; a mix | E-02 |
| O-08 | Narration generated at build time (admin reviews it) or runtime (unreviewed)? | Build time; runtime | Follows O-07 |
| O-09 | Credentials for the SAP Notes tool beyond the demo | Service/technical S-user; per-learner login; admin-only access | Needs confirmation (R-01) |
| O-10 | Tech stack, LLM, vector DB, BM25 library, graph storage, parsing tools, diagram technology, storage | Not discussed | Decide per slice, starting with what E-01 needs |

## Planned experiments

### E-01 Retrieval grounding spike (personal test, document grounding only)

Goal: prove the fan-out retrieval pipeline returns the right SAP content, and resolve O-01 to O-06.

- **Corpus:** one TADM unit plus one HANA Administration Guide chapter. Small enough to check by hand.
- **Validation set, written before building:** 20 to 30 queries, each with the expected canonical object IDs. Mix exact identifiers (TCodes, parameters), natural-language questions, procedure questions, concept-relationship questions, and 3 to 5 out-of-scope questions.
- **Configurations:** R0 vector only; R1 parallel fan-out with fusion; R1 plus enrichment and rerank.
- **Measures:** correct object in top 5; rank of first correct result; context noise; procedure step order complete; latency; context tokens; out-of-scope questions correctly flagged.
- **Rule:** score retrieval before any LLM answers, so a strong model cannot hide weak retrieval.

### E-02 Course format test

Goal: choose the display format (O-07) by learner outcome, not preference.

- Build one lesson from the same content model in two formats.
- Test with 2 or 3 trainees; measure a short quiz score and ask what confused them.
- Record which learner failure each format addressed.

## Risks and items needing confirmation

| ID | Item | Why it matters | Owner / next step |
| --- | --- | --- | --- |
| R-01 | SAP Notes tool runs on a personal account and automates the SAP support portal with Playwright | Fine for a personal demo; a shared or production version needs approved credentials and a check of SAP's terms for automated access | Confirm with manager before showing it as the target design |
| R-02 | Handoff says SAP Notes/KBAs are on-demand, not ingested; latest discussion mentioned ingesting me.sap.com documents including KBAs and Notes | If Notes are ingested, D-09 and the ingestion design change | Confirm which me.sap.com content is ingested vs retrieved on demand |
| R-03 | SAP training system access for hands-on exercises | Manager calls integration a must; it cannot be built without a system | Present as planned, pending approval; request access |
| R-04 | Few TADMs available | Corpus may be thin for some topics; the course builder may lean on the HANA guide | Inventory available documents before E-01 |

## Diagram change list (SAP\_AI\_COACH.svg)

- [ ] Ingestion: fix typo "Injestion" to "Ingestion".
- [ ] Ingestion: add parser profile labels (TADM, SAP Help / HANA guide) inside the parsing box (D-01).
- [ ] Main agent: replace Query Router with a parallel fan-out to BM25, vector and structured lookup (D-03).
- [ ] Main agent: add a "Fuse by canonical ID" step between the stores and Enrichment (D-04).
- [ ] Main agent: label the input (learner query) and output (grounded answer with citations).
- [ ] Tool Registry: add SAP System Integration Tool as a dashed box marked "planned, pending system access" (R-03).
- [ ] Tool Registry: collapse MCP client/server into the SAP Notes Retrieval Tool for the main deck; keep internals for the appendix.
- [ ] Course builder: rename the history store to show it is admin-only (D-11); add a course content store between Finalised module and UI.
- [ ] New diagram: learner journey and interaction (D-14).


## Implementation decisions — expanded E-01, 26 September 2026

| ID | Decision | Status | Evidence / reason |
|---|---|---|---|
| D-20 | Keep original and expanded corpus runs as separate datasets; reuse R0/R1 policies and canonical source IDs. | Implemented | Corpus growth changes retrieval difficulty; do not compare algorithms on different inputs without identifying the dataset. |
| D-21 | Score complete source evidence and ordered procedure steps separately from top-5 anchor hits. | Implemented | A correct procedure anchor can still yield one step instead of the whole procedure. |
| D-22 | Use a bounded, reviewed-candidate graph channel and explicit shared-concept aliases; preserve original source claims and edition qualifiers. | Experimental | Expanded graph adds one complete-evidence result, while some rankings regress; no production publication. |
| D-23 | Use real RAGAS ID metrics broadly and LLM context metrics on a declared, budgeted sample. | Implemented | Semantic usefulness and literal evidence-ID coverage answer different questions. Same-model judging is supplementary, not expert ground truth. |
| D-24 | Provide one offline comparison dashboard with question-type filters, reference answers, source evidence and procedure checklists. | Implemented | Make strengths and failure modes understandable in presentations rather than showing only JSON and averages. |
| D-25 | Maintain a root SESSION_LOG.md with reconstructed earlier history clearly labelled and current actions/reasons recorded. | Implemented | Preserve why changes were made and separate evidence from retrospective assumptions. |
| D-26 | Keep R1 with bounded source expansion as the default; leave R2 routing deferred. | Current experiment conclusion | Complete text evidence: R0 27/45, R1 ranking 32/45, R1 context expansion 40/45, R1 + graph 41/45 on 50 mixed questions. Larger independent cross-chapter evaluation is still needed. |

Implementation artifacts and limitations: [expanded findings](output/e01/expanded/report.md), [comparison dashboard](output/e01/dashboard.html), [decision/action history](SESSION_LOG.md).

## Implementation decisions — fresh E-01 benchmark, 28 September 2026

| ID | Decision | Status | Evidence / reason |
|---|---|---|---|
| D-27 | Keep parameter grouping as an explicit source-profile extension, retaining canonical IDs and atomic context budgets. | Experimental | It recovers E17 on the observed set; no matching profile occurs in the fresh chapters, so it has no effect there. |
| D-28 | Evaluate question-only LLM decomposition with a bounded deterministic selection policy as a separate variant. | Experimental | Observed set improved 42→44/45; fresh set remains 32/45, with one complete gain and one regression. Do not promote it solely on the observed-set gain. |
| D-29 | Freeze questions and retrieval policies before running a disjoint fresh corpus; keep results as a separate dashboard dataset. | Implemented | 109 unseen pages and 50 questions expose weaker transfer and new selection/parser/gold-reference failures. This is not a cumulative-corpus load test. |
| D-30 | Use the same declared semantic RAGAS sample for every fresh variant, including ranking-only R1. | Implemented evaluation design | Makes sampled comparisons fair; strict ID completeness can miss semantically equivalent alternate evidence. Frozen labels are not revised after seeing scores. |

Fresh results and limitations: [fresh benchmark](output/e01/fresh/report.md). The source-expansion default and graph/decomposition opt-in status remain unchanged.

## Implementation decisions — candidate pool and reranking, 28 September 2026

| ID | Decision | Status | Evidence / reason |
|---|---|---|---|
| D-31 | Diagnose misses by candidate-pool position before adding ranking components. | Implemented | Fresh R1: 19/22 missing items were in the fused pool at ranks 6–16, 3 at channel ranks 21–50, none deeper or unindexed. Oracle reorder ceiling 43/45 (pool 20), 45/45 (pool 50). |
| D-32 | Cross-encoder reranking of the whole fused R1 pool, anchor-only input (resolves the O-03 test in favour of anchor-only for now). | Experimental — strongest result so far | Cohere rerank-v4.0-pro: fresh 31→41/45 at top 5 with fewer tokens, 43/45 at top 10; expanded 40→43; original unchanged 21/21; zero regressions. Needs an unseen set, a self-hostable/approved reranker check, and latency budget before becoming the default. |
| D-33 | Keep top-5 as default; treat top-10 as a separate lever measured alongside rerank. | Experimental | Top-10 without rerank: fresh 31→37 at ~1.5× tokens; rerank top-10 adds 2 more over rerank top-5. |

| ID | Hypothesis / open item | Status | Test |
|---|---|---|---|
| H-01 | R2 variant: classify the query (or each decomposition facet) as exact-identifier / conceptual / procedural etc., and add class-specific weight to channels in fusion. | Hypothesis, deferred | Must name the failure it fixes beyond rerank. Remaining fresh misses are pool-recall (N02, N30) and multi-facet selection (N26, N37), not channel-weight errors. Compare against rerank on an unseen set. |
| R-05 | Cohere call used a rate-limited (likely trial) key and sent SAP training text to an external API. | Needs confirmation | Trial keys are not for production/commercial use; confirm data-sharing approval (also applies to AIcredits) and compare a self-hosted reranker (e.g. BGE reranker) before relying on Cohere. |

Artifacts: [candidate-pool diagnosis](output/e01/candidate_pool/report.md), [rerank report](output/e01/rerank/report.md), [dashboard](output/e01/dashboard.html). O-02 (fusion) remains open; O-06 (insufficient-context signal) is not answered by uncalibrated rerank scores.

## Implementation decisions — NVIDIA paired variants, 30 September 2026

| ID | Decision | Status | Evidence / reason |
|---|---|---|---|
| D-34 | Use `nvidia/llama-nemotron-rerank-1b-v2` for the new rerank experiments. Preserve Cohere runs as history. | Implemented adapter; API scoring pending | User-selected model; NVIDIA_API_KEY will be supplied later. No quality or latency result yet. |
| D-35 | Compare grouped hybrid + decomposition + Nemotron with/without graph, each at top 5 and top 10. | Four variants prepared | Hold plans, grouping, source corpus and 4096-token budget constant; isolate graph contribution within this pipeline. |
| D-36 | Rerank the canonical-ID union of all original/facet fused candidates against the original question. | Implemented | Avoid discarding useful facet candidates at the old five-anchor round-robin stage; no gold-aware selection. One ranking serves both cutoffs. |

Prepared artifacts: `output/e01/nemotron/`; workflow: `e01/nemotron/README.md`. These are follow-ups on observed datasets, not a new unseen evaluation. R1 default is unchanged until measured promotion.

### D-34 model correction and evaluation — 30 September 2026

User corrected the requested model to **`nvidia/llama-nemotron-rerank-vl-1b-v2`**. This supersedes the text-model name in D-34; the new run uses text inputs only. API scoring is complete: both graph/no-graph families score 42/45 expanded and 39/45 fresh at top 5; 43/45 expanded and 42/45 fresh at top 10. Graph inclusion has no completeness effect in these paired runs. Keep experimental: previously seen sets, no semantic RAGAS rerun, and comparison with historical Cohere changes more than the reranker alone. See `output/e01/nemotron/report.md`.

## Separate subquery scoring — 30 September 2026

| ID | Decision / hypothesis | Status | Evidence |
|---|---|---|---|
| D-37 | Independently rerank each facet's retrieved pool; original best + one unique facet hit each + original-ranked fill, same 5/10-anchor budget. | Tested, opt-in | Fresh improves 39→41 at top 5 and 42→43 at top 10; expanded top 10 regresses 43→42. One-hit reservations still miss second-ranked facet evidence. No default promotion. |
| H-02 | Render reviewed graph relations with predicates, direction, qualifiers and citations as prose for reranking. | Future experiment | Graph source passages already scored; relationship semantics currently omitted from reranker input. Must measure whether added relation text improves relevance without introducing unsupported claims or excessive latency. |
| D-38 | Keep observed redundant/alternative-evidence label issues separate from frozen experiment scoring. | Retained | N30 extra source ID appears redundant; N02 object-category coverage needs semantic audit. Any revised gold should be separately versioned. |

## Chatbot and diagrams — 2 October 2026

| ID | Decision | Status | Reason / boundary |
|---|---|---|---|
| D-39 | Freeze retrieval development while building other project parts. | User-directed freeze | Hash manifest in coach/retrieval_freeze.json; existing R1 expanded source-expansion default used unchanged. Experiments and alternative variants retained as history. |
| D-40 | React + FastAPI + native clickable SVG for the first chat/diagram slice. | User-selected; implemented | Semantic selection integrated directly; draw.io/MCP validation deferred. |
| D-41 | Diagrams are structured grounded teaching artifacts with stable per-artifact element IDs and canonical source references. | Implemented | Renderer has no retrieval; server resolves selections within their conversation, following D-07/D-08. Citation validation is not a semantic correctness guarantee. |
| D-42 | Local SQLite conversation/artifact storage and single-process API execution for this slice. | Local prototype only | Enables persistent follow-ups without deciding production storage/authentication/concurrency. |

Implemented workflow and known limits: `coach/README.md`. R1 default is not a claim that retrieval evaluation is complete; further optimization is deliberately paused by the user.

## Standalone app and framework memory — 2 October 2026

| ID | Decision | Status | Reason / boundary |
|---|---|---|---|
| D-43 | LangGraph StateGraph with InMemorySaver for learner conversations. | User-directed, implemented | Replace the app's custom SQLite chat storage with framework thread memory; later evaluate another checkpointer/context policy on longer chats. Restart clears new threads; old SQLite history archived. |
| D-44 | Make coach/ independently runnable with bundled frozen retrieval assets and its own frontend/config. | Implemented | Main app no longer imports parent-project experiments or reads their assets/keys. Copied retrieval algorithms remain unchanged and hash-checked. |
| D-45 | Preserve validated answer text when an optional diagram fails checks; expose an explanatory notice. | Implemented regression fix | Actual model response combined insufficient status with a diagram; earlier code incorrectly discarded the entire answer and showed a generic budget/API error. Invalid factual citations still fail closed. |

D-42's SQLite choice is superseded for active chat memory by D-43. Answer generation remains AIcredits `openai/gpt-5.6-luna`, configured in coach/config.json; no Astra migration requested.

## Conversation quality fixes — 2 October 2026

| ID | Decision | Status | Reason / boundary |
|---|---|---|---|
| D-46 | Resolve query intent before retrieval; standalone topics discard history and stale selections for generation too. | Implemented | Observed SUM context contaminated Maintenance Planner questions. Same configured LLM resolves references; no new agent or ingestion. One extra intent call on contextual turns. |
| D-47 | Use existing NVIDIA VL reranker with top-ten anchors in the app adapter. | Implemented for requested evidence-selection fix | Indexed task content was absent from plain top-five results. Frozen algorithms unchanged; graph/decomposition experimental variants are not enabled. Three-turn replay is not a broad benchmark. |
| D-48 | Separate learner follow-up suggestions from clarification requests; support partial explanations/diagrams and grouped page citations. | Implemented | Fix speaker reversal and over-caution without inventing missing facts. Source-ID checks are not entailment validation. |

## App package ownership — 2 October 2026

| ID | Decision | Status | Reason / boundary |
|---|---|---|---|
| D-49 | App-owned retrieval package with a stable retrieve(message, history, selection) result contract; experiments remain outside deployment. | User-directed, implemented | Replaces nested runtime/e01 layout and experiment-specific checks; future algorithms can be promoted behind the service injection boundary. App ranking behavior preserved in cached replay. |
| D-50 | Separate offline ingestion package with reviewable candidate indexes and explicit activation. | Implemented | PDF extraction/normalization/chunking/embedding belongs outside chat requests. Edition-specific profiles, no automatic graph extraction or corpus append. |
| D-51 | Project-root .venv and .env, app-owned assets under coach/data. | User-directed, implemented | Run from coach with ../.venv/bin/python run.py; no external temporary environment or experiment assets required. Supersedes the earlier coach-local credentials and frozen runtime snapshot layout. |
