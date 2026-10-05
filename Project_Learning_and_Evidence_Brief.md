# SAP AI Learning Agent — Project Learning & Evidence Brief

Prepared 2 Oct 2026 from: `SAP AI Learning Agent — Design Decision Log.md`, `SESSION_LOG.md`, `handoff.md`, `old/spec.md`, `output/e01/**/report.md` (extraction, expanded, fresh, candidate_pool, rerank, nemotron), `coach/reviews/2026-10-02-chat-review.md`, `coach/README.md`, `coach/.data/quality_check/*.json`.

Status labels used: **Established** (artifact or log evidence exists) · **Partial** (evidence exists with stated limits) · **Not established yet** (no evidence found).

---

## 1. The problem

**What:** LTM SAP BASIS freshers (mostly CSE/ECE graduates, new to SAP) learn from dense official material — TADMs such as ADM328 (S/4HANA Conversion & Upgrade) and the SAP HANA Administration Guide. The initial ask from the manager was vague: "an AI learning platform / interactive chatbot on official SAP training material."

**Why it matters:**
- SAP-specific factual errors are costly for a BASIS trainee (wrong parameter, wrong procedure step order). So *grounding with mandatory citations* was a primary requirement, not a nice-to-have.
- The material is structurally hostile to naive RAG: multi-page numbered procedures, nested sub-steps, tables without repeated headers, parameter references split across objects, figures carrying knowledge, assessments with answers on separate pages.
- Secondary goal: give the SAP BASIS BU a technically credible GenAI/agent initiative (stated in handoff §2).

**Evidence:** handoff §1–2, spec §1. Established.

---

## 2. What I actually built or changed (chronological)

| Date | Work | Evidence |
|---|---|---|
| ~3 Sep | Wrote a PoC spec (sections 1–7): two agents, tool registry, TADM knowledge architecture | `old/spec.md` |
| 23–24 Sep | Reworked into "SAP AI Learning Agent — Solution Overview" deck after manager feedback; 19 recorded design decisions (D-01…D-19), open-decision list, planned experiments E-01/E-02 | `presentation/*.pptx`, decision log |
| 24 Sep | **E-01 extraction**: document-specific PDF parser (PyMuPDF) for TADM and HANA-guide profiles; 29 pages → 440 canonical source objects; 29 source-backed checks; 26 questions written *before* retrieval | `output/e01/extraction_report.md` |
| 24–26 Sep | **R0** (local BGE-small vector) vs **R1** (BM25 + vector + structured lookup in parallel, RRF fusion by canonical ID, bounded procedure/source expansion) | session log |
| 25–26 Sep | LLM-extracted knowledge graph with provenance + review gates; opt-in graph retrieval channel; interactive graph viewer | `output/e01/expanded/graph/` |
| 26 Sep | **Expanded corpus**: 113 pages, 1,673 objects, 50 questions; RAGAS (isolated env); offline comparison dashboard | `output/e01/expanded/report.md`, `dashboard.html` |
| 27 Sep | Failure trace of the 4 remaining misses; parameter grouping; LLM query decomposition variant | `failure_analysis/report.md`, `decomposition/` |
| 27–28 Sep | **Fresh, disjoint benchmark**: 109 unseen pages, 50 questions hash-frozen before retrieval; 7 variants | `output/e01/fresh/report.md` |
| 28 Sep | **Candidate-pool diagnosis** (ranking loss vs recall loss) + oracle ceiling, then top-10 and Cohere rerank | `candidate_pool/report.md`, `rerank/report.md` |
| 30 Sep | NVIDIA Nemotron VL rerank paired with/without graph; independent per-facet reranking | `nemotron/report.md` |
| 2 Oct | Froze retrieval (hash manifest). Built learner app: FastAPI + React + clickable SVG diagrams with semantic element IDs; LangGraph (intent → retrieve → generate → validate → commit) | `coach/` |
| 2 Oct | Reviewed real chat sessions, found 5 issues, fixed them, regression-tested | `coach/reviews/2026-10-02-chat-review.md`, `coach/.data/quality_check/` |
| 2 Oct | Made the app standalone: app-owned retrieval package with a stable `retrieve(message, history, selection)` contract; separate offline ingestion package that builds candidate indexes and never overwrites the active one | `coach/README.md`, D-49–D-51 |

**Not built yet:** Course Builder Agent, voice narration, SAP Notes tool, SAP system integration, figure understanding, authentication/multi-user, course UI.

---

## 3. Important technical decisions (with the failure each solves)

| Decision | Failure it solved | Status |
|---|---|---|
| Document-type parser profiles → shared canonical model (D-01) | Generic chunking flattens TADM pedagogy and HANA hierarchy, losing citation location and procedure integrity | Implemented for 2 profiles |
| Removed the query router; parallel fan-out instead (D-03) | Router misroutes silently drop the right channel; routing was unproven | Held throughout; router still deferred |
| Merge channels by canonical ID before enrichment (D-04) | Same object from two channels duplicated in context | Implemented |
| Score complete evidence & ordered procedure steps separately from top-5 hit (D-21) | "Correct anchor found" hid that only 1 of 5 procedure steps reached the context | Implemented — key metric choice |
| Score retrieval *before* any LLM answer (E-01 rule) | A strong LLM masking weak retrieval | Followed |
| Freeze questions & policies before running the fresh corpus (D-29) | Tuning on seen questions inflating results | Followed; exposed decomposition overfitting |
| Diagnose candidate-pool position before adding a reranker (D-31) | Adding a component without knowing whether misses were recall or ranking | Done; justified rerank |
| Anchor-only reranker input (resolves O-03 for now) | Enrichment text adding noise to relevance scoring | Experimental |
| Diagram tool does no retrieval; every grounded node/edge carries canonical source ID; explanatory nodes flagged (D-07, D-08, D-41) | Diagrams drawn from ungrounded content; selections that can't be resolved back to sources | Implemented |
| Native clickable SVG over draw.io MCP (D-40) | Needed semantic selection IDs; draw.io's ID preservation unvalidated | Implemented |
| Optional diagram failure must not discard a valid answer (D-45) | Real crash: model returned "insufficient" + diagram → whole answer dropped | Fixed with regression fixture |
| Intent-resolution node before retrieval (D-46) | Previous-topic text contaminated a new question's retrieval | Fixed, replayed |
| Partial-answer status (D-48) | Whole-answer "insufficient" suppressed useful supported teaching | Implemented |
| Retrieval freeze + stable retrieval interface (D-39, D-49) | Endless retrieval tuning blocking the rest of the product; experiments leaking into the app | Implemented |

---

## 4. Trade-offs I considered

- **Rerank vs fusion change vs wider top-k.** Diagnosis showed equal-weight RRF demotes single-channel hits (e.g. N37: vector rank 1 → fused rank 9). I measured three levers separately: top-10 without rerank (fresh 31→37 at ~1.5× tokens), rerank top-5 (31→41 with *fewer* tokens), rerank top-10 (43/45 = oracle ceiling). Fusion re-weighting stays an open alternative (O-02).
- **Quality vs governance for the reranker.** Cohere `rerank-v4.0-pro` scored best at top-5 (fresh 41/45) but ran on a rate-limited trial key and sent SAP training text to an external API (R-05). The app uses NVIDIA `llama-nemotron-rerank-vl-1b-v2` (median 693 ms vs Cohere 945 ms). The comparison is not isolated — pipelines differed. *Exact reason for choosing NVIDIA beyond R-05: not recorded.*
- **Graph value vs cost/risk.** Graph needed ontology design, extraction, two review gates, alias registry and hash-pinned review — for +1 complete question per dataset, with regressions (Q01/Q05 rank 1→3; N28 lost evidence). Kept opt-in, not used in the app.
- **Decomposition gain vs regression risk.** +2 on the seen set, zero net on fresh, plus a new failure class. Kept opt-in.
- **Strict ID completeness vs semantic correctness.** Strict labels penalise equivalent alternate evidence (N30, N39). I kept labels frozen rather than rescoring after seeing results, and reported the limitation.
- **Paid evaluation scope vs cost.** RAGAS semantic metrics on a declared, fixed sample (n=8 recall / n=4 precision) rather than everything; deterministic ID metrics on all questions.
- **Bounded chat memory.** LangGraph InMemorySaver with 12-message / 16k-character window; restart clears threads. Chosen for this slice, not production.

---

## 5. What failed or didn't work as expected

1. **Knowledge graph under-delivered.** Expanded: 79 provenance-valid edges → 53 enabled after review (85 proposals rejected, 14 uncertainties). Gain: 40→41 complete. Fresh: 31→32, with N28 regressing. In paired NVIDIA runs, graph inclusion changed **zero** outcomes. Root cause noted: entity matching ignores *which relationship* the question asks about.
2. **Query decomposition overfit the observed set.** Expanded 42→44/45; fresh stayed 32/45 (gained N11, lost N16, N02 worsened). N22: the planner split a "complete deletion procedure" question into prerequisites/backups/follow-ups and *dropped the procedure itself* — JSON validation could not catch the semantic omission.
3. **Parameter-grouping fix was too narrow.** Recovered E17 on the expanded set (41→42), but no matching structure existed in the fresh chapters → zero effect.
4. **Per-facet reranking** helped fresh (39→41) but regressed expanded top-10 (43→42, E24). Not promoted.
5. **Benchmark quality didn't transfer to the app.** First real chat review: 4 of 5 answers "insufficient". The app was running plain R1 top-5 (not the best benchmarked variant), and an app heuristic prepended the previous question to any message under ten words — reproducibly contaminating "what does a maintenance planner do" with an earlier SUM error question.
6. **Follow-up suggestion speaker reversal.** Assistant clarification questions were rendered as one-click learner messages; the model then answered "Yes" to its own question.
7. **Crash on valid answer.** Model returned `insufficient` + a diagram; validator rejected the whole response, surfaced as a generic error that looked like budget exhaustion.

---

## 6. Bugs, blockers, constraints

| Blocker | Workaround |
|---|---|
| HANA table detector found 0 tables on 9 stress pages; text-based detection over-segmented columns | Recovered cell boundaries from segmented horizontal rules; regression check caught header-row bug |
| Large bullet glyphs classified prerequisites as headings | Heading detection requires textual font evidence |
| Empty checkbox glyphs extract as "X" in assessments | Did not guess answers; assessments excluded and queued |
| Hard-coded "Unit 3" heading marker broke later units | Fixed; extracted each unit independently; verified all 440 original objects unchanged |
| Repeated numbered sequences / nested restart substeps | Procedure normalisation; 17 procedures with valid top-level numbering |
| Nested table instructions mistaken for procedure numbering (fresh HTTPS) | Quarantined before freezing gold/index; issue kept |
| Torch not installable in VM (CUDA wheels exhausted disk) | NumPy forward pass of the same BGE weights; verified max abs diff 2.4e-7 and exact ranking reproduction |
| Egress proxy blocked Cohere/AIcredits | Domain allowlisted by user |
| Cohere 10 calls/min (trial key) | Wait-and-retry; excluded wait time from latency |
| Dependency break: newer langchain-community removed a module RAGAS imported | Isolated RAGAS env, pinned 0.3.31 |
| RAGAS / NVIDIA request timeouts with unknown charge | Single explicit retry; kept original reservation in ledger; no silent retries |
| Browser policy blocked visual preview of local HTML | Syntax/data/link checks + one headless render; *no full visual QA* |
| Small budget (~$5 envelope initially) | Request-hash caching, per-stage caps, usage ledgers |
| No SAP training system access | Integration shown as "planned, pending access" (R-03) |

---

## 7. Non-obvious insights

1. **"Found the right chunk" ≠ "can answer."** On the expanded set, R1 ranking found the GUI conversion procedure at rank 2 but only 1/5 steps reached context; bounded procedure expansion made it 5/5. Measuring *complete evidence* instead of top-k hit rate changed which component looked important: source expansion was the biggest single win (32→40), not the graph.
2. **Locate the miss before choosing the fix.** 19/22 fresh misses were already in the candidate pool at ranks 6–16; none were unindexed. That turned "do we need better embeddings / more data?" into "we need better ordering", and gave a ceiling (43/45) before spending on a reranker.
3. **A reranker can improve completeness and reduce context.** Rerank top-5 completed 10 more fresh questions while using fewer tokens (493→467 mean).
4. **Retrieval benchmarks don't catch conversation bugs.** The worst user-visible failures were in the app layer (history prefix heuristic, follow-up roles, answer/diagram validation coupling), not in the retrieval algorithm.
5. **Gains on seen questions are not evidence.** Decomposition and parameter grouping both looked good until a frozen, disjoint set was used.
6. **RAGAS can rate relevant-but-incomplete context highly.** E14: R0 ≈100% semantic precision but 11% semantic recall; step checklists exposed the gap.
7. **LLM self-review isn't enough for graph edges.** Same-model review still missed optional-vs-required and wrong-predicate errors; human source inspection was needed.

---

## 8. Assumptions I changed my mind about

| Earlier assumption | What changed it | Now |
|---|---|---|
| Route-specific retrieval (spec FR-16) | No evidence fan-out was too noisy; remaining misses were ranking/selection, not channel weighting | Router deferred (H-01) |
| Knowledge graph would be central to retrieval | +1 question, regressions, zero effect in paired runs | Opt-in experiment; not in app |
| Reranker needed (spec FR-18) — assumed | Tested only after diagnosis showed ranking loss | Now evidence-backed |
| Weak answers = need more ingested data | Chat review: relevant passage was indexed but not selected; app bugs dominated | Fix app first, then targeted ingestion |
| draw.io MCP for diagrams | ID preservation for click-to-ask unproven | Native SVG with semantic IDs |
| Custom SQLite chat history | Requested framework memory | LangGraph InMemorySaver (local only) |
| Frame as "PoC" | Manager feedback | "SAP AI Learning Agent — Solution Overview" |
| Voice = read the course aloud | Discussion | Voice is an output channel; UX to be tested (E-02 not run) |

---

## 9. Tools, frameworks, techniques

Python, PyMuPDF (layout-aware extraction), BGE-small-en-v1.5 (local embeddings), BM25, Reciprocal Rank Fusion, canonical-ID merging, bounded source/procedure expansion, LLM knowledge-graph extraction with provenance + review gates, LLM query decomposition, Cohere Rerank v4.0 pro, NVIDIA Nemotron rerank VL, RAGAS 0.4.3 (ID + LLM context metrics), MRR, oracle-ceiling analysis, request-hash caching + budget ledgers, hash-pinned freezes, FastAPI, React/Vite, SVG, LangGraph StateGraph + InMemorySaver, OpenAI-compatible LLM via AIcredits (`gpt-5.6-luna`), pytest-style offline regressions.

---

## 10. Measurable results (all retrieval-level, not answer accuracy)

**Complete required text evidence** (strict: every labelled source block present in context):

| Dataset | R0 vector | R1 hybrid + expansion | Best variant |
|---|---:|---:|---|
| Original (29 pp, 21 text Q) | 14/21 | 21/21 | — |
| Expanded (113 pp, 45 text Q) | 27/45 | 40/45 | 44/45 (graph+grouping+decomp; seen set) · 43/45 Cohere rerank |
| Fresh, unseen (109 pp, 45 text Q) | 24/45 | 31/45 | **41/45 rerank top-5 · 43/45 top-10 (= oracle ceiling)** |

- Fresh full-procedure completeness: R0 1/7 → R1 expansion 6/7.
- MRR R1 → Cohere rerank: 0.724→0.856 (original), 0.674→0.833 (expanded), 0.776→0.903 (fresh).
- Zero regressions vs R1 for Cohere rerank on all three datasets.
- Latency (serial API, not load-tested): local search ~35 ms; Cohere median 945 ms; NVIDIA median 693 ms.
- Total paid evaluation spend reported by providers ≈ ₹40 across graph pilot, expanded and fresh work (not wallet-reconciled).
- App: 18 offline tests pass; 3-turn live regression (Stack XML → "Okay so what does Maintenance Planner do?" → "Explain its role in upgrades.") went from wrong-topic/insufficient answers in the review to grounded, cited answers including the actual task list.

**Caveats you must keep:** questions and gold references were assistant-authored/extractive, *not SAP-expert validated*; fresh questions became "observed" after diagnosis (promotion needs a new unseen set); semantic RAGAS samples are tiny (n=4–8) and use the same model family as extraction.

---

## 11. Stakeholder / user feedback

- **Manager (Established, on the deck):** don't frame as "PoC"; use stronger technical terminology for SAP audience; show admin steps explicitly in Course Builder; add end-to-end user journey slides; move retrieval detail to appendix; SAP system integration is "good and a must"; voice narration requested.
- **Senior principal director presentation (D-18):** planned; *outcome not recorded*.
- **Trainee/learner feedback:** *Not established yet.* E-02 (format test with 2–3 trainees) not run.
- **Your own usage as a learner:** real chat sessions reviewed on 2 Oct — this is self-testing, not user feedback.

---

## 12. Artifacts (and public-safety check)

| Artifact | Shows | Public-safe? |
|---|---|---|
| Results tables above (numbers only) | R0→R1→rerank progression | Yes, as aggregated numbers |
| Candidate-pool funnel (in pool rank 6–16 / 21–50 / not indexed) | The diagnosis insight | Yes — redraw as a simple chart |
| Architecture diagrams in the Solution Overview deck | Two agents, tool registry, ingestion | Needs employer approval; remove LTM-internal names |
| Offline comparison dashboard (`output/e01/dashboard.html`, 50 MB) | Variant comparison, procedure checklists | **No as-is** — embeds ADM328/HANA text and figures (SAP copyrighted training material). Screenshot with redaction only |
| Graph viewer (`expanded/graph/graph.html`) | Entity/edge provenance | Redacted screenshot only |
| Learner app (cited answer + clickable diagram + selected-node follow-up) | The product working | No screenshot captured yet (`POC_images/` is empty) |
| Decision log format (Decision / Status / Failure it solves) | Engineering method | Yes, with generic examples |
| Repo | — | No git repo; not public |

---

## 13. What I personally contributed

Evidenced by the logs as yours:
- Problem framing from a vague ask; stakeholder management with manager; deck reframing.
- Manual inspection of TADMs → observations that shaped ingestion (unit objectives, concepts introduced before their lesson, repeated assessments with answers, figure-heavy content) — handoff §7.
- The "what failure are we solving by adding this component?" rule and the decision log discipline.
- Direction of experiments and key questions: asking whether misses were *ranked out or never reached the pool*; proposing query decomposition; spotting the N30 redundant-label issue; proposing graph relations rendered as prose for reranking (H-02); choosing to freeze retrieval and move to the product; choosing stack (React + FastAPI + SVG, LangGraph) and reranker model.
- Reviewing real chats and authorising the five fixes.

**Important honesty note:** the session log is written as "User requested… / implemented…", which indicates much of the code, extraction and evaluation execution was done with an AI coding assistant under your direction. Not established: which code you wrote by hand. A credible post should say you *designed, directed and evaluated* the system with AI-assisted implementation, and not imply you hand-wrote every component. No teammates are recorded — appears to be a solo project with a manager stakeholder.

---

## 14. Still incomplete or uncertain

- No independent SAP-expert validation of questions/gold answers.
- No new unseen set after the rerank decision; app reranker choice not validated on one.
- O-06 (when to say "insufficient") untested; reranker scores are uncalibrated.
- Figures: 75 untranscribed in the fresh chapters alone; captions only. Headerless tables not indexed.
- Citation checks verify ID membership, not factual entailment.
- No end-to-end latency, no concurrency/load test (target was ~40 students).
- Course Builder, voice, SAP Notes tool, SAP system integration: not built.
- Corpus: ~222 pages sampled from two manuals; the running app uses only the 113-page expanded index.
- Data governance: SAP text sent to Cohere, NVIDIA and AIcredits APIs — approval not confirmed (R-05).
- No visual browser QA of the app.

---

## 15. What I'd do differently next iteration

- Write a frozen unseen test set **at the start**, and treat every set used for diagnosis as burned.
- Run the candidate-pool diagnosis *before* the graph and decomposition experiments — it would have pointed to ranking first and saved the graph effort.
- Start real conversational testing earlier; the app-layer bugs were cheaper to find than retrieval gains.
- Get an SAP-expert to validate even 10–15 gold answers.
- Settle data-governance approval before sending source text to external APIs.
- Capture screenshots and timings as I go.

---

## 16. Relevance to the engineer/FDE I'm becoming

FDE work is turning a vague customer ask into a scoped, measurable system inside real constraints. This project shows: requirement discovery with a non-technical stakeholder; domain-specific ingestion instead of generic RAG; evaluation designed so the LLM can't hide retrieval failures; willingness to keep negative results (graph, decomposition) instead of shipping them; diagnosis before adding components; budget and data-governance awareness; and the shift from benchmark to product by reviewing real conversations.

---

# Summary sections

## 1. Project in one sentence
I'm building an SAP AI Learning Agent that teaches BASIS trainees from official SAP manuals with mandatory citations and clickable diagrams, and I used evaluation-driven experiments to decide which retrieval components actually earn a place.

## 2. Strongest accomplishment
Diagnosing *why* retrieval failed before adding anything: on a frozen, disjoint 109-page benchmark, 19 of 22 missing evidence items were already in the candidate pool at ranks 6–16. That justified a reranker, which raised complete-evidence questions from 31/45 to 41/45 at top-5 (43/45 at top-10, equal to the oracle ceiling) with fewer context tokens and zero regressions.

## 3. Technical learnings
1. Measure *complete evidence* (all procedure steps present), not "relevant chunk in top-k": R1 found the GUI conversion procedure at rank 2 but delivered 1/5 steps until bounded procedure expansion made it 5/5.
2. Equal-weight RRF demotes strong single-channel hits (vector rank 1 → fused rank 9), so a hybrid fusion step can create the very misses you blame on embeddings.
3. Locate misses in the candidate pool (and compute an oracle ceiling) before choosing between more data, better embeddings, fusion weights or a reranker.
4. Retrieval benchmarks don't test conversations: a "prefix short messages with the last question" heuristic silently contaminated topic switches.
5. Optional generated artifacts (diagrams) must fail independently of the grounded answer; coupled validation turned a recoverable issue into a crash.

## 4. Mistakes/failures and what they taught me
1. **Knowledge graph:** a lot of design and review effort for +1 question, some regressions, and zero effect in paired runs → measure the cheaper levers (expansion, rerank) before building structural components, and match on relationships, not just entities.
2. **Decomposition looked good on seen questions** (42→44) but gave no net gain on fresh ones and dropped the task in one case → freeze questions before testing; seen-set gains are hypotheses, not results.
3. **Strong benchmark, weak app:** the first real chats were mostly "insufficient" because the app ran a weaker retrieval config plus a buggy history heuristic → evaluate the product path you actually ship, with real conversations.

## 5. Most interesting engineering trade-off
Reranking vs fusion re-weighting vs wider top-k, measured separately on the same pool: top-10 alone bought +6 at ~1.5× tokens; rerank top-5 bought +10 with *fewer* tokens; rerank top-10 hit the ceiling. Secondary trade-off: the best-scoring reranker (Cohere, trial key, external data transfer) vs a governance-friendlier choice — still not cleanly resolved.

## 6. Evidence/results I can safely claim
- On a 109-page benchmark with 50 questions frozen before retrieval (45 text-answerable): vector-only 24/45 → hybrid + procedure expansion 31/45 → + cross-encoder rerank 41/45 complete required evidence (43/45 at top-10).
- Full-procedure completeness 1/7 → 6/7 with hybrid + bounded expansion.
- Rerank: zero regressions across three datasets; MRR 0.776 → 0.903 on the fresh set.
- Graph channel: +1 question per dataset, with regressions; kept experimental.
- Working local app: cited answers, partial-answer handling, clickable SVG diagrams whose elements map to source IDs, LangGraph conversation memory, 18 offline tests.
- Must say alongside: retrieval-level metrics only, assistant-authored gold, not SAP-expert validated, small corpus, no load test, not used by trainees yet.

**Do not claim:** answer accuracy, hallucination rate, learner improvement, production readiness, latency at scale, cost per learner, or that trainees use it.

## 7. Artifacts worth showing
1. A redrawn results chart: R0 → R1 → R1+expansion → rerank (fresh set).
2. Candidate-pool funnel diagram (where the misses actually were).
3. App screenshot: cited answer + diagram + "ask about this node" — **capture this first**.
4. Generic architecture diagram (two agents, tool registry, canonical knowledge layer) after employer review.
5. Decision-log excerpt: "Decision | Status | Failure it solves."
Never post raw dashboard/graph screenshots containing SAP manual text.

## 8. Potential LinkedIn angles
1. **"Before adding a reranker, I checked where the misses were."** Diagnosis → 31→41/45. Strongest, most evidence-backed.
2. **"The knowledge graph that didn't earn its place."** An honest negative result; good signal of engineering judgment.
3. **"My retrieval benchmark passed; my chatbot still failed."** Benchmark vs product; three app-layer bugs found in real chats.
4. **"One question I ask before every component: what failure does this solve?"** Method post using the decision log.
5. **"Why 'top-5 hit rate' lied to me about procedures."** Complete-evidence metric and procedure expansion.

## 9. Missing information to capture before you forget
- App screenshots/GIF of the chat + diagram + selection follow-up (none exist).
- Outcome and feedback from the director presentation (D-18), and the manager's reaction to the E-01 results.
- Written permission from LTM/your manager to post publicly, and what may be named (LTM, SAP, ADM328).
- Why you chose NVIDIA over Cohere for the app (beyond R-05).
- Your role split: what you designed/decided vs what the AI assistant implemented; hours spent; dates.
- Any end-to-end response time from the running app.
- Whether the earlier diagram SVG (`SAP_AI_COACH.svg`, referenced in the log) still exists — it wasn't in the folder.
- Before/after screenshots of the Maintenance Planner conversation (the JSON exists in `coach/.data/quality_check/`).
- One sentence from a trainee, even informal, if you can get one.

## 10. LinkedIn milestone check

| Criterion | Met? | Evidence |
|---|---|---|
| Something works now that didn't before | **Yes** | Running app with cited answers & clickable diagrams; Maintenance Planner chat fixed from wrong-topic to grounded |
| Meaningful stage complete | **Yes** | E-01 retrieval evaluation complete and frozen; first app slice shipped locally |
| Learned something non-obvious by doing | **Yes** | Misses were ranking not recall; RRF demotion; seen-set gains didn't transfer |
| Real technical decision/trade-off | **Yes** | Router removed; graph kept opt-in; rerank vs top-k vs fusion; retrieval freeze |
| External evidence (feedback/usage/recognition/metrics) | **Partial** | Measurable benchmark results and manager feedback on the deck; no learner usage or recognition |
| Tangible artifact | **Partial** | Dashboard, graph viewer, deck exist but need redaction; no app screenshot yet |
| Explainable in 2–3 sentences without exaggeration | **Yes** | See §1 and §2 above |

**LinkedIn-eligible: Yes**

Two conditions before posting: (1) get employer/manager approval and keep SAP manual content out of any image; (2) take an app screenshot or redraw the results chart so the post has a safe visual.
