# SAP Coach implementation session log

This log distinguishes reconstructed earlier work from actions recorded as they occur. Dates reflect the working session (25–26 September 2026); exact earlier timestamps were not recorded. Source artifacts remain the detailed evidence.

| Step | Decision / action | Reason | Result / limits |
|---|---|---|---|
| Earlier, reconstructed | Inspected root design documents and both PDF families; extracted ADM328 Unit 3 and HANA Chapter 7 | Validate E-01 on a inspectable slice before whole-document ingestion | 440 canonical objects; figures preserved but not understood; checkbox answers deferred |
| Earlier, reconstructed | R0 pinned local BGE-small-en-v1.5 vector retrieval | Establish a cheap reproducible baseline | 15/21 text anchor hits; 14/21 complete text evidence on original questions |
| Earlier, reconstructed | R1 parallel BM25, vector and structured lookup with RRF, then bounded source expansion | Recover exact identifiers and full procedures | 19/21 text anchor hits; 21/21 complete evidence after enrichment; seen regression set, not general accuracy |
| Earlier, reconstructed | AIcredits GPT-5.6 Luna graph pilot; correct endpoint from official documentation | User supplied API key/provider and roughly $5 credit budget | Seven entity types, eight predicates, 22 scoped nodes; nine supported candidate edges after source inspection; six calls reported ₹2.26 |
| Earlier, reconstructed | Strict provenance plus separate semantic review | Exact quotes alone cannot establish relation correctness | Broad SLD claim rejected; repeated-mention bug fixed; same-model audit still missed questionable identity/membership |
| Earlier, reconstructed | Offline interactive graph viewer | Make entities, directed edges and source evidence inspectable | graph/pilot/graph.html; browser visual preview blocked by local-file URL policy; syntax/data checks passed |
| 25 Sep | Opt-in R1 + graph channel, one hop, nine supported candidates | Measure graph value without changing baseline | Same 21/21 complete evidence; MRR .724→.743; two rank improvements and two regressions; 28 relevant tests passed |
| 26 Sep | Expanded corpus stored separately under output/e01/expanded | Avoid invalid comparisons and preserve original R0/R1 artifacts | Same original question IDs carried forward; new labels versioned independently |
| 26 Sep | Add ADM328 Units 4–6, HANA Chapter 5 and Chapter 8.1–8.3.1.1.5 | Introduce connected administration/conversion concepts and multi-page procedures | Scope chosen from PDF outlines; not full manuals |
| 26 Sep | Fix hard-coded Unit 3 heading matching; extract added ranges independently | Preserve correct unit parents and prevent assessment numbering from mixing across units | Original extracted objects reused unchanged |
| 26 Sep | Use isolated RAGAS environment; source-grounded reference answers; no generated student answers | Evaluate retrieval without allowing answer generation to hide missing evidence | Deterministic coverage remains primary; LLM judge scores are supplementary |
| 26 Sep | Initial expanded paid-work ceiling: $1.50 USD-equivalent reserved across graph and evaluation, retaining original $5 overall envelope | Controlled measurable expansion | Costs and exact requests will be cached and logged; no full-manual paid run |

## Recorded expansion actions and reasons

| Action | Reason | Outcome |
|---|---|---|
| Read additional PDF outlines and source passages using the PDF skill; visually inspected HANA restart page 64 | Scope new chapters and distinguish nested transaction substeps from top-level actions | Added ADM328 53–108 and HANA 38–43 / 62–83; total 113 pages |
| Extended the initial HANA endpoint from 77 to 83 | Near-zero conversion continues on page 78; complete isolation subsection ends on 83 | No procedure deliberately cut at the original planned boundary |
| Extracted each added training unit separately, reusing old inventory verbatim | Avoid cross-unit assessment pairing and duplicate procedure construction | 1,673 objects; all 440 originals identical; all eligible text lines assigned |
| Corrected repeated numbered procedure sequences and nested restart substeps | A whole lesson can contain several procedures; substep 1 is not necessarily a new procedure | 17 procedures; valid top-level numbering, eight top-level restart steps |
| Excluded headerless table objects/rows from indexing | Flattened cells without column labels are unreliable evidence | Conservative index gate; no header inference |
| Created 24 new source-authored questions and reference answers before expanded retrieval | Cover cross-chapter, exact identifiers, negative conditions, version scope and full procedures | 50 questions total; 45 text-answerable, one visual, four unsupported |
| Added an optional dataset path to Hybrid; built separate expanded vectors | Run identical retrieval policies on a larger corpus without overwriting original runs | 810 anchors, 819 BGE windows; original default paths unchanged |
| Extended provisional ontology with artifact/privilege types and uses/produces/invokes | New chapters contain named files, roles and tool/process interactions missing from pilot vocabulary | Nine entity types and eleven predicates; still an experimental ontology |
| Ran 14 cached extraction batches over 416 source objects, then seven review batches | Grow graph from source text independently of validation labels | 237 raw entity records; 79 provenance-valid edges; 85 rejected proposals |
| Inspected all 79 retained edge quotes/predicates/qualifiers; recorded 14 uncertainties | Model review misses optional-versus-required and wrong-predicate errors | 53 edges enabled after both review gates and one table-to-index exclusion |
| Added 13 explicit shared-concept registry entries; retained original endpoint IDs and evidence scope | Test cross-section linking without merging arbitrary equal strings or deployed instances | 206 entity records after merges; product/tool aliases are auditable |
| Hash-pinned the reviewed graph before enabling the inspection script | Recorded assistant decisions must not silently approve new extraction output | Changed graph output fails closed and requires a fresh source inspection |
| Added bounded two-hop lookup only through reviewed shared identities | Test whether interlinked source concepts return useful additional evidence | Max five graph source objects; 10 two-hop paths appeared in the saved query audit |
| Installed RAGAS 0.4.3 in a separate environment; pinned langchain-community 0.3.31 | Newer community package removed an imported module; preserve original retrieval environment | Working dependency lock saved; telemetry/tracing disabled |
| Used real RAGAS ID metrics on the full eligible set, plus predefined semantic samples | Broad deterministic evaluation with bounded paid judging | ID metrics for original and expanded datasets; semantic recall n=8 and precision n=4 per R0/R1/graph variant |
| Kept ID precision labelled as reference-ID overlap | Required-evidence labels are not exhaustive relevance judgements | Dashboard avoids claiming all unlabelled passages are noise |
| Used exact cached judge requests across variants | Avoid repeated costs and stochastic differences for identical contexts | Graph evaluation reused baseline judgments where inputs matched |
| Corrected the restart procedure's Further Information boundary after preliminary source QA | A supplementary blog link is not part of the last action | Reference revision v2; final index/retrieval rerun; question wording and answer claims unchanged |
| Built a common offline dashboard rather than replacing historical results | Show strengths, failures and completeness across implementations and corpus sizes | Dataset/cohort/type/outcome filters, per-step checklists, source links, RAGAS sample sizes, graph paths and presentation mode |
| Updated graph layout to handle reciprocal edges and shared concepts | Directed cycles made simple topological columns collapse | Breadth-first layout; expanded view opens on lifecycle-manager connections |
| Ran 28 existing hybrid/graph tests and seven expanded checks | Verify source preservation, full procedures, graph gates, coverage, RAGAS consistency and budgets | 35 tests passed; Python and browser-script syntax checks also performed |
| Kept graph opt-in and deferred R2 | Measured gain is small and entity-only graph matching still causes regressions | R0 27/45, R1 ranking 32/45, R1 expanded context 40/45, graph 41/45 complete evidence |

## Interpretation and remaining limitations

The expanded graph recovers the high-isolation requirement question, but the HDBLCM and Solution Manager cross-chapter cases still have missing evidence. RAGAS judges some relevant-but-incomplete contexts highly on precision; recall and explicit step checks reveal the missing answer content. Graph extraction and RAGAS use the same model family, and references remain assistant-authored/source-extractive rather than SAP-expert gold.

Figures, checkbox interpretation, unsupported-question abstention, production graph publication, a query router (R2), answer generation, and a 40-student load test remain unimplemented. No SAP system actions were performed. Automated visual preview of local HTML is blocked by browser URL policy; syntax/data/link checks are the current UI verification boundary.

## Status

Expanded ingestion, versioned questions/references, graph growth and opt-in integration, actual RAGAS evaluation, common dashboard, and this decision/action log are complete for the bounded experiment. See output/e01/expanded/report.md for final metrics and response-reported costs.


## 2026-09-27 — Diagnose the four remaining R1 + graph failures

User requested tracing only the questions still incomplete before ingesting more chapters. Added `e01/expanded/diagnose_failures.py` and a separate audit under `output/e01/expanded/failure_analysis/`; preserved retrieval code, graph, gold, dashboard, and baseline results.

- Replayed E05, E11, E17, E24 locally and asserted exact top-five and assembled evidence-ID agreement with saved results. All four passed. No paid calls.
- Confirmed all missing passages are indexed, none has a retained graph edge citing it, and no context expansion was budget-excluded.
- E05: BM25 rank 3 loses in fusion (R1 6, graph 7); graph proposals had an ungrounded process mention and unresolved endpoint. Not safe to approve by fixing the missing word alone.
- E11: conversion rank 25; proposed edge quote omitted its recorded process mention. Literal query linking also missed the lifecycle-manager name without the SAP prefix.
- E17: parameter heading, description, and syntax are separate objects without exact keys; description was excluded from graph inputs by the 70-character filter. Recommend source-structure grouping first.
- E24: graph model received the passage but proposed no edge for it; vector rank 7 falls to graph rank 17. Cause of model omission remains unknown.
- Recommended sequence: bounded parameter grouping; graph provenance-repair/linking experiments with review gates; controlled multi-part retrieval comparison; then unseen chapters after freezing implementation. These are proposed experiments, not implemented architecture decisions.

Report: `output/e01/expanded/failure_analysis/report.md`; reproducible evidence: `trace.json`. Analysis used extracted source objects and cached model outputs; no new PDF visual review or independent expert certification.

## 2026-09-27 — Parameter grouping; query-decomposition idea deferred

User authorized grouping and suggested simplifying/splitting questions to retrieve both halves. Explained that bounded query decomposition could help multi-part questions, while a shorter paraphrase alone does not guarantee coverage. Retained this as a future paired experiment; no rewriter implemented.

Implemented an opt-in `ParameterGroupedHybrid`, with a default-preserving `Hybrid.context_units` extension. Derives complete parameter entries from Parameter Reference sections and matching CLI identifiers, preserves canonical source IDs, excludes related-information links, and applies the existing atomic context budget. No ranking, graph, embedding, or gold changes. A group exact key is recorded but adds no search vote in this isolated experiment.

Ran all 50 questions with and without the graph: top-five rankings match saved baselines; no existing evidence lost. Only E17's evidence changed: 50% to 100%, 132 to 286 context tokens. Complete evidence improves R1 40→41/45 and graph 41→42/45. The remaining graph failures are E05, E11, E24. No paid calls or semantic RAGAS rerun. 38 tests passed, including new grouping-boundary and regression checks. Earlier dashboard scores remain historical; separate review/report are in `output/e01/expanded/parameter_grouping/`.

Scope limit: three recognized parameter entries and one affected known benchmark case; this does not establish unseen generalization. Future decomposition should preserve constraints and original query, cap subqueries/context, and measure both gains and regressions on independent questions.

## 2026-09-27 — R1 + Graph + Decomp

User explicitly requested implementing query decomposition as a new R1 variant, explaining the intelligence, and updating the dashboard with grouping and decomposition results.

- Used the existing AIcredits model `openai/gpt-5.6-luna` as a question-only planner. Five batches of ten questions; no source passages, graph, expected answers or required IDs supplied. Cap: $0.35, eight calls, three subqueries per question. Network preflight failed inside sandbox; reran with required network escalation. Five paid calls completed and cached; response-reported approximately ₹0.534, conservative reservation $0.0300.
- Planner classified 22/50 questions as multi-part. Its plans remain unchanged for evaluation, including imperfect wording; structural/identifier checks do not claim semantic equivalence. No hard-coded decompositions for known failures.
- Implemented a separate variant using grouped parameter context and the same graph/search channels. Selection reserves original best hit then alternates unique facet hits, with the same five anchors and 4096 tokens. This evaluates decomposition plus selection, not a wording-only change.
- Replayed the grouped graph baseline ranking for all 50 queries. Complete evidence improves 42→44/45; E05 and E24 recovered, E17 retained, E11 still incomplete. No previously complete question or required-evidence coverage regressed. Other source evidence was displaced on some questions; no precision guarantee is claimed.
- E11's missing passage reaches rank 3 in its conversion subquery but is excluded by the final five-source selection. Documented this as a candidate-selection limitation; did not tune a special rule or expand the cutoff for it.
- Ran actual RAGAS ID recall/overlap precision for both grouping variants and decomposition. Semantic judging not rerun; dashboard marks new semantic scores Not scored. Added all follow-up variants, model plans, selected-hit origins, and subquery traces to the common dashboard, preserving historical results.
- 43 tests passed; dashboard payload/data consistency and generated JavaScript syntax checked. No new browser visual verification or production latency/concurrency claim. Local timings exclude the batched LLM planning stage.

Artifacts: `output/e01/expanded/decomposition/` and common `output/e01/dashboard.html`. Default baseline retrieval remains unchanged; this is an opt-in experiment. Next evaluation should use unseen source-authored questions after freezing this implementation.

## 2026-09-27–28 — Fresh chapters, frozen seven-way benchmark

User requested a new chapter set similar in size to the current corpus, approximately 50 new questions, all R0/R1 variants, and a dashboard update. Work resumed from saved artifacts after the conversation interruption; all 17 graph extraction and seven model-review calls had finished and were reused without duplicate spending.

- Selected disjoint ADM328 Units 7–8 (PDF 109–162) and HANA PDF 84–138: 109 pages versus the earlier 113. This is a fresh-only corpus, not a cumulative-index experiment. All variants use identical source/index inputs within this dataset.
- Preserved retrieval-policy hashes before fresh evaluation. Refactored the existing procedure-normalization helper for reuse and allowed the unchanged index recipe to take a dataset path. No retrieval tuning after fresh results.
- Extracted 1,458 source objects; 2,579 eligible lines assigned; indexed 814 anchors / 817 windows. Visually inspected ADM328 PDF 117 and HANA PDF 105. A nested-table HTTPS procedure has malformed top-level numbering and was quarantined before indexing/gold freezing; source objects and issue remain. Two headerless tables and untranscribed figures remain limitations.
- Source-authored and froze 50 questions before retrieval: 45 text, one visual, four unsupported. Seven full procedures and comparisons/cross-section questions are included. Gold remains assistant-authored/extractive, not independent expert validation.
- Built graph with the existing ontology/extraction recipe: 84 provenance-valid candidates. Inspected all quotes/endpoints/predicates/qualifiers; marked ten additional uncertainties and excluded unindexed table evidence. 47 edges enabled, 229 entity records after 11 reviewed shared aliases. Source-review hash contract pins the decisions; no production approval implied.
- Reused the frozen question-only decomposition prompt and selection policy. Planner split 35/50 questions. It sees no expected answers, required IDs, graph or retrieval output.
- Fresh complete-evidence results: R0 24/45, ranking-only R1 28/45, source-expansion R1 31/45, graph 32/45, grouped R1 31/45, grouped graph 32/45, decomposition 32/45. No parameter-reference groups matched this corpus, so grouped results equal their base variants.
- Graph gains N05/N06 but regresses N28. Decomposition gains complete N11, loses complete N16, partially improves N37 and worsens N02. N22 reveals a planner semantic failure: procedure steps were omitted from its subqueries. These findings are preserved, not patched during the benchmark.
- Label audit found redundant-required-ID cases (N30), equivalent alternate evidence (N39), and incomplete nearby cautions/follow-up in N22's procedure-derived gold. Recorded limitations without changing frozen labels or rescoring.
- Added a separate Fresh chapters dataset to the common dashboard, selected by default, with all seven variants, fresh cohort filter, subquery plans/traces and a fresh report link. Historical datasets remain available.
- Actual RAGAS ID metrics cover all 45 text questions for every variant. Matched semantic sample: eight recall/four precision questions for all seven variants, selected before retrieval; semantic run in progress at this log entry. Caps: graph $0.85, planning $0.35, RAGAS $0.65. Same model-family judge and offline planning-latency limitations remain.

### Fresh benchmark completion — 28 September 2026

Completed the matched RAGAS sample for all seven variants: 56/56 recall judgments and 28/28 precision scores. R0 sampled recall/precision: 53.2%/87.5%; ranking-only R1: 60.6%/77.9%; source-expansion R1 (and grouped): 89.6%/91.7%; graph (and grouped graph): 95.8%/94.6%; decomposition: 95.8%/98.8%. The declared sample excludes the observed N02/N16/N28 regressions, so these high sample averages do not establish a net decomposition benefit on the full set.

One RAGAS request hit the 90-second transport timeout. Its charge remains unknown; original reservation retained and hash recorded in `ragas/timeout_audit.json`. One explicit retry succeeded within the unchanged $0.65 cap, and all completed requests were cached. No automatic repeated retry or ledger deletion. RAGAS: 64 attempts, 63 usable cached responses, one timed-out reservation.

Fresh work response-reported costs: graph ₹13.607, decomposition ₹0.700, RAGAS ₹5.786 = approximately ₹20.09, excluding any unknown charge on the timed-out request. Total conservative reservations $0.8300, within the combined $1.85 ceilings. Cost figures are provider response fields, not a reconciled wallet balance.

Validation complete: 28 existing hybrid/graph tests, 15 expanded follow-up tests, and five fresh benchmark tests passed (48 total). Verified source-page disjointness, frozen policy/gold/input hashes, seven variants on the same 50 questions, source provenance/review gates, budget limits, actual RAGAS ID agreement, and identical semantic sample membership. Generated dashboard/graph JavaScript syntax and dashboard source IDs/data checked. No automated browser visual verification.

The shared dashboard now defaults to Fresh chapters, with all seven variants visible and all historical datasets retained. The fresh report records gains, regressions, narrow grouping coverage, gold-reference limitations, and next experiments. No retrieval changes were made in response to fresh outcomes. This authorized benchmark task is complete.

## 2026-09-28 — Candidate-pool diagnosis (ranking vs recall)

User asked whether missing evidence was ranked out or never reached the top 20, to bound reranker value. Added read-only `e01/fresh/diagnose_candidate_pool.py` and `e01/fresh/oracle_rerank_ceiling.py`; outputs in `output/e01/candidate_pool/`. No retrieval, gold or policy changes; no paid calls.

- Replay gates passed: saved top-5 reproduced for all 36 incomplete variant-questions; fresh channel top-20 lists reproduced (27/27).
- Torch was not installable in the Cowork VM (CUDA wheels exhausted disk); used a numpy forward pass of the same pinned BGE weights, verified against stored vectors (max abs diff 2.4e-7) and exact ranking reproduction.
- Fresh R1: 22 missing items across 14 questions. 19 items/12 questions are in the fused pool at ranks 6–16; 3 items/2 questions (N02, N30) are at channel ranks 21–50; none deeper or unindexed. Expanded: all 5 in pool.
- Oracle reorder of current pool: fresh 31→43/45; with channel_k 50: 45/45. Label-free top_k 10: 37/45 at ~1.6× tokens.
- Equal-weight RRF demotes single-channel hits (e.g. N37 vector rank 1 → fused 9); fusion is a competing hypothesis to a reranker. N30/N39 gains would be label artifacts.
- Conclusion: failures are ranking/selection, not recall. No component added; reranker remains a hypothesis to test against fusion change and top_k 10 on an unseen set.

## 2026-09-28 — Top-10 and Cohere rerank follow-up (in progress)

User asked to test (a) expanding 10 anchors instead of 5 and (b) Cohere Rerank over the existing R1 candidate pool, on the existing original, expanded and fresh sets, then update the dashboard. Query-type classification feeding weighted fusion (an R2 idea) deferred until rerank results are in; corpus expansion deferred until both experiments finish.

- Added `e01/rerank/rerank_experiment.py` (prepare/apply/ids) and stdlib-only `e01/rerank/cohere_rerank.py` (cached per request hash, usage ledger, 200 search-unit cap, key read from root .env and never logged). Outputs under `output/e01/rerank/`. No R1 policy, gold, index or earlier result changes.
- `prepare` replayed frozen R1 on all 126 questions and asserted saved top-5 for each before exporting pools (22–40 candidates; 3,831 documents). Rerank documents are anchor-only: section path + the anchor's own source units (O-03 anchor-only option).
- r1_top10 (label-free, same 4096-token cap, no reorder): original 21/21 (unchanged), expanded 40→42/45, fresh 31→37/45. Mean context on eligible questions: 1,792 / 1,367 / 753 tokens. No budget exclusions on fresh.
- ID recall/overlap precision for new variants computed with the RAGAS ID formulas directly; verified identical to the saved RAGAS library scores on 180 fresh+expanded r1/r1_graph rows.
- Cohere step blocked: both the Cowork VM and cloud workspace egress proxies reject api.cohere.com (and api.aicredits.in from the VM). User is adding the domain to the allowlist. Default model rerank-v4.0-pro.
- Dashboard: added r1_top10, r1_rerank, r1_rerank_top10 names/descriptions to the template and a follow-up loader in `dashboard.py`; existing variants, datasets and layout unchanged. Rebuilt; embedded JavaScript syntax checked.

### Rerank completion — 28 September 2026

User added api.cohere.com to the egress allowlist. `cohere_rerank.py` ran from the Cowork VM: 126 requests, 126 billed search units, all cached; 429 rate limits (10/min, consistent with a trial key) handled by waiting, not billed. Four early calls timed the 65 s wait into latency and are excluded from latency figures; the client was then fixed to time only the successful attempt.

- Complete text evidence — original: all variants 21/21. Expanded: R1 40, top-10 42, rerank 43, rerank top-10 43 /45. Fresh: R1 31, top-10 37, rerank 41, rerank top-10 43 /45 (equals the oracle ceiling for the 20-per-channel pool).
- MRR R1 → rerank: 0.724→0.856, 0.674→0.833, 0.776→0.903. Rerank top-5 uses fewer context tokens than R1 on every dataset.
- No regressions against R1 or R1 + graph on any dataset. Remaining fresh misses N02/N30 are outside the pool (as diagnosed); N26/N37 recover at top-10; expanded E11/E24 remain.
- Cohere API median 945 ms/query (p90 1.8 s) versus ~35 ms local search; not a load test.
- Dashboard rebuilt with r1_top10, r1_rerank, r1_rerank_top10 on all three datasets (format unchanged); ID recall shown, semantic RAGAS marked Not scored. Headless render checked: ten cards, RAGAS table, no page errors.
- Caveats recorded: N39/N30 label cases; fresh questions previously observed (no rerank tuning on them, but promotion still needs an unseen set); SAP source text sent to Cohere; trial keys are not for production/commercial use.
- Deferred, per user: query-type classification feeding weighted fusion (R2 idea), to be scoped against rerank results; corpus expansion after both experiments.

Report: `output/e01/rerank/report.md`.

## 2026-09-30 — NVIDIA Nemotron + decomposition, paired graph experiment

User requested `nvidia/llama-nemotron-rerank-1b-v2` and two new R1 families, each with top-5/top-10 outputs: grouped hybrid + query decomposition + rerank, with and without graph. Credentials will be supplied later.

- Added `e01/nemotron/client.py` and `experiment.py`, plus reproduction notes/tests. NVIDIA hosted endpoint and query/passages/index/logit schema verified against official documentation. Uses only `NVIDIA_API_KEY`; no AIcredits/Cohere credential reuse. No NVIDIA calls made.
- Both families retain parameter grouping and procedure expansion. Search original question and saved LLM facets, fuse each search, then union every fused candidate by canonical ID. Graph evidence enters only the graph family. Rerank the union against the original question before selecting 5/10 anchors; no premature old five-hit round-robin selection. Context budget stays 4096 tokens.
- Reused existing decomposition plans and reviewed graphs on expanded/fresh sets (50 questions each); original dataset remains historical. Baseline R1 top-five ranking replay passed for all 100 questions. Source/code/input hashes pinned with the prepared pools.
- Prepared 200 family/question pools, maximum 69 expanded / 78 fresh candidates; 146 unique API payloads after exact request deduplication. One full ranking supplies both top-5/top-10, avoiding duplicate calls. No fabricated results or semantic scores.
- Rerank text contains section path plus each anchor's own source units; no local character clipping. Explicit API `truncate=END` can truncate oversized query/passage pairs. Logits are relevance scores, not calibrated confidence.
- Added durable pre-request ledger, exact payload/endpoint cache, 200-attempt cap, response-index/finite-score checks, and stop-on-failure with no implicit retry. Attempt cap is not a monetary-cost guarantee. Shared search timing includes both families and excludes offline planning; not a production latency comparison.
- Restored missing local dependencies in `/tmp/sap-nemotron-venv`; seven tests passed for canonical union/origins, graph isolation, top-k/context budgets, payload/cache identity, score mapping, cache reuse and uncertain-attempt handling. Prepared-pool checks confirmed unique IDs and no graph channel in graph-free pools.
- Dashboard adds pending NVIDIA status now and loads four scored variants only after complete cached response application. Historical Cohere and baseline outputs retained. NVIDIA scoring and semantic RAGAS remain pending.

## 2026-09-30 — NVIDIA VL correction and completed evaluation

User corrected the model to `nvidia/llama-nemotron-rerank-vl-1b-v2`, supplied NVIDIA_API_KEY through .env, and authorized scoring/dashboard/log updates.

- Changed model and hosted endpoint to the documented VL version; regenerated prepared payloads and source/code hash manifests before scoring. Same text-only inputs, saved plans, graph gates, candidate policy and gold; no vision evaluation. All 100 original R1 ranking replay checks passed again.
- Completed 146 unique NVIDIA requests, all cached, no failed attempts. Both top cutoffs reuse the same full response ranking. Median API latency 693 ms, p90 1232 ms; this is serial benchmark API latency, not a load test. Usage token fields retained; monetary charges not supplied/reconciled.
- Expanded: graph-free and graph families each 42/45 complete at top 5, 43/45 at top 10. Top-10 misses E05/E11. Fresh: both families 39/45 at top 5, 42/45 at top 10. Top-10 misses N02/N05/N30. No completeness regressions versus plain R1; graph inclusion produces no complete/incomplete changes between paired NVIDIA families.
- Cohere historical results remain 43/45 expanded and 41/45 fresh at top 5; 43/45 both at top 10. This comparison changes model AND pipeline (decomposition/grouping/candidate pools), so it is not an isolated model ranking. No automatic promotion or tuning from these results.
- Applied cached ranks to four actual result sets per dataset, added deterministic ID recall, and generated `output/e01/nemotron/report.md`. Semantic RAGAS not rerun; references and known label limitations unchanged.
- Dashboard now loads all four scored variants on expanded/fresh, identifies Nemotron VL and text inputs, and shows API timing/cutoff. Corrected decomposition-selection wording to describe reranking instead of the old round-robin selector. Original/Cohere history preserved.
- Seven local tests passed. Checked full response-index permutations, all 400 output question rows, context budget, required-ID coverage, graph-free candidate isolation, dashboard JSON/source references and JavaScript syntax. No browser visual verification performed in this session. No key values printed or saved in artifacts.

## 2026-09-30 — Independent facet reranking and protected selections

User authorized separate subquery scoring/testing and raised two follow-ups: N30's redundant evidence label, and rendering graph relations as prose for reranking.

- Preserved frozen labels. N30 already retrieves an explicit unsupported-feature statement; missing the extra “Nothing. The feature is not supported.” ID is a known strict-label artifact. N02 contains detached object-category bullets; do not assume these are redundant without checking semantic coverage. No benchmark score silently revised.
- Added `e01/nemotron/facets.py`: reconstruct each subquery's own candidate pool from saved search-origin membership, rerank against that subquery using the same NVIDIA VL model, preserve original-query best result, reserve one distinct hit per facet, then fill from original-question ranking. Same 5/10 total anchors, grouping/procedure expansion and 4096-token cap. No raw-score comparison across queries; no query-specific tuning. Single-mode questions reuse original results.
- Separate frozen configs, results, ID scores, report and API ledger under `output/e01/nemotron/facets`. 169 unique additional successful requests. One request timed out; recorded one explicit retry via `retry_facet_timeout.py`, retaining original unknown-charge attempt. Total 170 attempts, 169 completed; no repeated automated retries, no duplicate billing from cache hits claimed.
- Paired graph/no-graph completeness remains identical. Fresh top 5: 39→41/45 (N05/N26 gains); fresh top 10: 42→43/45 (N05 gain). Remaining fresh top-10 cases N02/N30. Expanded top 5 unchanged 42/45; expanded top 10 43→42/45 (E24 regression).
- E05/E11 missing passages improve from whole-question rank 17 to their facet rank 2, but the fixed one-hit facet reservation does not select them. E24's new reserved selection displaces required evidence previously at original rank 10. Preserved these outcomes rather than retuning the rule on observed questions.
- Reported mean serial original+facet API time ~1.9–2.4 seconds depending on dataset/family, excluding offline planning and timeout retry; not a production load test. Semantic RAGAS not rerun. Model/pools/labels unchanged from the prior NVIDIA experiment apart from separate scoring/selection.
- Dashboard adds four facet variants, accurate selection descriptions, all selected anchors with selection origin, and per-subquery reranked top-five traces. Older NVIDIA/Cohere results retained. Ten local tests passed; all 400 new output rows checked for budgets, ID coverage, source mapping, unique selections and unchanged single-query contexts; dashboard JSON/JavaScript checked. No browser visual verification.
- Future graph idea recorded, not implemented: render typed relationships as faithful sentences including direction, qualifiers and citations, to inform reranking. Current graph source passages already undergo reranking; relation text itself does not. Generic “is/are” insertion can distort meaning. Extra latency/quality is unmeasured and depends on input length/call design; retain source evidence rather than treating generated relation prose as authoritative quotes.

## 2026-10-02 — Retrieval frozen; chatbot and interactive diagram slice

User explicitly froze retrieval development while other project parts are built, then selected React + FastAPI + native clickable SVG rather than a draw.io/MCP spike.

- Recorded SHA-256 freeze manifest in `coach/retrieval_freeze.json` over existing e01 code/configs and expanded runtime index artifacts. No e01 algorithm, labels, benchmark output or dashboard changes. Runtime uses the established R1 source-expansion default on expanded chapters, top five / 4096 retrieved tokens. No new reranker/graph/decomposition experiment.
- Built FastAPI teaching service and React/Vite local learner workspace: ask questions, cited answer paragraphs, PDF page links, optional grounded diagrams, select nodes/edges, ask about the selected element, and persist local conversations/artifacts in SQLite. SQLite is a local implementation choice, not final shared-user storage. React/SVG renderer performs no retrieval.
- Defined bounded semantic diagram/answer schema. Server validates citation IDs against supplied evidence, unique element IDs, valid edge endpoints and explicit explanatory-only flags. Saved artifact UUID + node/edge IDs support selection; canonical source IDs remain independent of generated artifact IDs. Model never returns executable SVG/HTML.
- Diagram follow-ups resolve artifact/element IDs from server-owned conversation history; another conversation cannot submit an unrelated selection. Selected source passages are additional cited context, separately identified from the frozen 4096-token retrieval context. Short follow-ups use previous-question context via a simple app heuristic; retrieval code itself is unchanged.
- Reused existing AIcredits model/provider with a separate application ledger, $0.50 USD-equivalent reservation cap and 20-call ceiling; keys remain server-side. Local single-worker serialization prevents shared model/API-ledger races. No authentication, production concurrency, SAP system operations or deployment claimed.
- Five backend tests passed: retrieval hash freeze, unknown citation rejection, invalid diagram edge rejection, explanatory-node rules, conversation persistence and selection isolation. React production build passed. Three live smoke checks passed: grounded Maintenance Planner explanation plus two-node/one-edge diagram; selected-node follow-up; insufficient-evidence response for an unknown production password. Smoke responses retained under ignored `coach/.smoke/`; reservations total approximately $0.0227, not a wallet charge claim.
- App started on http://127.0.0.1:8000 after required localhost-bind escalation. No automated browser visual QA in this session. Run/setup/scope notes: `coach/README.md`. Frontend and backend dependencies locked separately.
- Next product work: user review of this first interaction; then improve teaching/conversation/diagram behavior based on observed failures. Freehand circling, diagram editing, course builder, voice, SAP Notes and shared-user authentication remain future work. Retrieval development stays frozen unless user explicitly reopens it.

## 2026-10-02 — Readable standalone coach, LangGraph memory, follow-up fix

User reported an error after the first Stack XML answer, requested readable main-app code, a self-contained coach directory, LangGraph orchestration/memory, and identification of the answer model.

- Root cause verified from server logs and the exact cached failed response: model returned status insufficient plus a diagram; `validate_answer` raised “Insufficient answers cannot assert a diagram”. Both provider responses were cached; only ~$0.0140 reserved across the two calls, so this was not budget exhaustion. No API call was required to diagnose it.
- Answer text/citations now validate independently of the optional diagram. Insufficient-evidence or structurally invalid diagrams are omitted with a visible notice; invalid answer citations still fail. Added exact cached-response regression fixture and distinct budget/provider/answer/application error codes. No invisible repeated generation or paid repair loop.
- Reorganized readable Python modules: settings, prompts, provider, retrieval adapter, contracts, service, LangGraph workflow, errors and HTTP routes. Formatted application Python and React/CSS. Frozen bundled retrieval files intentionally remain byte-identical.
- Standalone coach directory now contains its own config, ignored .env (existing AIcredits key copied locally, value never displayed), React source/build, source PDFs, pinned local embeddings and index, frozen retrieval snapshot and hash manifest. No runtime dependency on parent e01/docs/tmp/web/.env. Root experiment files and retrieval algorithms are unchanged. Legacy root web remains historical; active UI is coach/web.
- Implemented LangGraph StateGraph: retrieve → generate → validate → commit, with InMemorySaver per thread_id. Only validated completed turns enter chat history; failed calls do not. Thread state retains all turns, but generation receives at most 12 recent messages and 16,000 characters. This is a bounded window, not automatic summarization or long-term memory. Server restart clears sessions; prior SQLite database preserved as an unused archive.
- Answer model remains openai/gpt-5.6-luna via AIcredits (not Astra), visible in coach/config.json and /api/health. NVIDIA remains an experimental reranker rather than the answer model. Existing app usage ledger/cap preserved; no hidden budget reset.
- Eight tests passed: runtime integrity, exact reported failure recovery, optional-diagram failure isolation, bad text citation rejection, thread memory/isolation/restart, failed-turn exclusion, scoped selection/typed errors, history-window bounds. Frontend production build passed. Two live LangGraph calls successfully answered Stack XML then a selected-element follow-up; ~$0.0139 reserved in separate smoke ledger, not a wallet charge claim.
- Copied coach to an isolated /tmp location without credentials or parent-project files; verified local embedding load/retrieval and UI/API/PDF serving. First path assertion required resolving macOS /tmp→/private/tmp, then passed. No browser visual QA performed.
- Restarted local app at http://127.0.0.1:8000 using `python run.py` from coach/. User should refresh/start a new chat. Updated run/code-map/memory/error documentation in coach/README.md and pinned runtime/frontend dependencies. Retrieval development remains frozen.

## 2026-10-02 — Review real learner chats before further ingestion

User requested analysis of their results and identification of fixes before ingesting more data. Read-only review completed; retrieval/ingestion remain frozen, no new paid calls or app restart.

- Read five real post-refactor answers from two active local sessions and preserved snapshots in ignored coach/.data/review_2026-10-02. All five HTTP 200; four insufficient, one grounded; three optional diagrams omitted safely. Previous validation crash is resolved.
- Confirmed follow-up speaker reversal: assistant-addressed questions are rendered as learner-submit buttons; two submitted messages exactly match these suggestions, leading to role confusion/irrelevant explanation.
- Replayed the short-topic-change query. The app's <10-word previous-question prefix exactly reproduces the poor Maintenance Planner evidence set contaminated by a prior SUM/error-message query. This is app context handling, not LangGraph memory loss.
- Fresh Maintenance Planner question gets 160 tokens of weak context including a tasks caption/introduction and heading. A useful calculate-files passage already exists in the index but is not selected. Clarified that runtime is expanded-only plain R1, not the later benchmark rerank variants; more ingestion alone is not sufficient.
- Recorded proposals for partial-answer teaching, claim-scoped diagram support, learner-readable citations and precise edge labels. Kept limitations clear: caption-only figure handling, citation existence vs entailment, small observed sample, no current browser visual QA.
- Findings/priorities: coach/reviews/2026-10-02-chat-review.md. No fixes silently implemented; proposed app fixes precede further ingestion and any retrieval policy change must respect the freeze.

## 2026-10-02 — Fix learner conversation and evidence presentation

User authorized five fixes: follow-up speaker reversal, old-topic contamination, missed indexed evidence, overly cautious partial answers and citation presentation.

- Added an LLM intent node before retrieval. It resolves contextual messages using recent dialogue and selected-element metadata. Standalone questions remain verbatim and drop history/selection for retrieval AND answer generation. Genuine ambiguity asks a clarification without search/generation. First messages without history/selection skip the intent call. Exact identifiers/versions receive a structural preservation check; semantic correctness still depends on the model.
- Learner-worded follow-up suggestions are separated from assistant clarification requests. Prompt rules plus a defensive phrase filter prevent the observed role-reversal patterns from becoming submit buttons.
- Promoted existing NVIDIA llama-nemotron-rerank-vl-1b-v2 text ranking into the app adapter: unchanged fused R1 pool, rerank, ten anchors, unchanged 4096-token source expansion. Does not include experimental knowledge graph/facet decomposition. Frozen algorithms/index and historical dashboard benchmark results unchanged; hashes verified. coach/.env has the locally copied NVIDIA key without printing it. Separate exact-request cache/200-attempt ledger; no automatic retries or claims that AIcredits cap covers NVIDIA charges.
- Added partial answer status: explain supported material first, identify narrow missing details, permit supported diagrams. Unknown citations still reject an answer. Caption-only content is not treated as an unseen figure.
- Grouped citations per document/PDF page with expandable passages, readable titles and one link per group. Deduplicated source IDs and stripped raw IDs/provider citation markup from prose.
- Verification: 14 offline tests passed, including intent isolation, ambiguity routing, partial diagrams, speaker/citation cleanup, rerank ordering and frozen-policy restoration. Production frontend build passed. No browser visual QA performed.
- Live regression used six AIcredits calls (~$0.0305 reservations/accounting, not reconciled wallet cost) plus three NVIDIA requests. Initial run correctly switched from Stack XML to Maintenance Planner and retrieved the indexed task list, but exposed provider citation markup and over-cautious pronoun resolution. Fixed markup cleanup and recent-topic priority; resumed only the third turn within the same six-call/$0.08 cap. It correctly resolved 'Explain its role in upgrades' to Maintenance Planner and answered with citations. All three final turns grounded by model status; this is a small regression, not independent expert validation. Original and corrected results retained in ignored coach/.data/quality_check.
- Updated coach/README.md, .env.example, health retrieval label and developer regression tool. Existing app AIcredits ledger/caps preserved. Restarted local server; in-process threads cleared as documented. No new ingestion, graph layout/drag/zoom work or dashboard re-evaluation in this change.

## 2026-10-02 — App-owned retrieval/ingestion packages and project environment

User requested that coach run without the experimental e01 folder, have replaceable retrieval and separate ingestion packages, and use a virtual environment at the project root.

- Replaced the nested runtime/e01 snapshot with coach/retrieval: retriever entry point, hybrid/vector search, NVIDIA client, embedding configuration and versioned index contract. Removed experiment CLI/report/evaluation code, global import-path injection, gold-question dependencies and experimental source-hash checks. Search/context algorithms retained; top-ten cutoff is now an explicit context argument rather than a temporary global-policy mutation.
- Relocated PDFs, embedding weights and active inventory/passages/vectors to coach/data/documents, models and index. Index manifest checks four artifact hashes and embedding identity independently of physical model location. The app never reads parent experiments, output, docs or tmp.
- Added coach/ingestion with edition-specific deterministic PDF extraction, repeated-step normalization, chunking, validation and index building; coach/ingest.py supplies extract/build commands. Candidate outputs require new directories; failed extraction or existing/active indexes cannot be overwritten. Candidate selection uses SAP_COACH_INDEX and a restart. This builds a replacement corpus from specified ranges, not incremental automatic append. Image understanding and LLM graph construction are not added.
- Created SAP_COACH/.venv and installed app dependencies there; recorded the full environment in coach/runtime-lock.txt. API clients now use root .env or environment variables. Preserved existing root key values and moved the former local credentials file into an ignored migration backup without printing values. No environment or runtime dependency in /tmp remains; old environment was not deleted.
- Archived obsolete snapshot code/manifests under ignored tmp/coach_before_packages, outside the app; not a runtime dependency. Parent experiment code and benchmark results left unchanged.
- Verification: 18 offline tests pass from inside coach using ../.venv/bin/python check.py; pip check reports no broken dependencies. Three cached live-regression queries produce identical selected anchors and evidence under the new package. No new paid verification requests. Two-page PDF extraction → 10 objects → two passage embeddings → load/search passed; temporary candidate removed after testing, active corpus unchanged.
- coach/verify_standalone.py copies only coach (no keys/caches/node_modules/experiment directory), then validates UI, health, PDF serving, local search and module paths in a subprocess. Passed using the root environment. This verifies packaging/API behavior, not browser visual layout.
- Updated README with run/setup commands, ingestion workflow, retrieval interface and promotion boundaries. Restarted server from coach with ../.venv/bin/python run.py; local health responds. In-memory chats reset as documented. User can refresh http://127.0.0.1:8000.

## 2026-10-04 — Explain app source code with comments

- User requested explanatory comments throughout coach. Added comments to all 28 authored Python files and the React/CSS sources, focusing on request flow, LangGraph state/branching, source/citation validation, ranking mathematics, context assembly, PDF extraction/chunking, index integrity, cache/budget behavior, and frontend sessions/diagram selection. Generated assets, data, credentials and third-party code were not edited.
- Comment-only changes: compared Python ASTs and executable tokens during the main edits; verified exact recovery of original frontend/package/test files after removing inserted comments. All Python files parse; JSX/CSS transformation syntax checks pass. Model prompt strings and runtime behavior are unchanged. No paid calls, ingestion, dependency changes or server restart.

## 2026-10-04 — SAP-inspired frontend colors

- Replaced the green/cream palette with white and cool neutral surfaces, blue actions/links/selections and a dark navy navigation rail. Added shared CSS color variables and applied them to inline SVG arrows, nodes and labels, including selected diagram elements and checkbox accents. Preserved separate warning/error colors and existing layout/behavior.
- Rebuilt the production frontend successfully. No backend changes or paid calls; no browser visual inspection performed. Refresh the running app to load the new compiled assets.

## 2026-10-05 — Recover cited answers containing an uncited gap paragraph

- Investigated the actual cached add-ons response after the reported invalid_answer error. The model returned partial status, two cited paragraphs, a cited diagram, and an uncited paragraph describing missing material. The validator required citations on every partial-answer paragraph and discarded the whole result.
- Normalization now checks schema and unknown source IDs first, retains cited paragraphs when any exist, marks the result partial, and visibly discloses omission of uncited text. It does not classify uncited text as harmless by guessing from its wording, invent citations, or render uncited claims. All-uncited grounded/partial answers still fail. Diagram validation uses the accepted text envelope so an omitted paragraph does not unnecessarily discard a valid diagram.
- Added the exact cached response as a regression fixture plus a test that uncited technical claims are omitted and fabricated citation IDs remain rejected. No model prompt/schema changes, cache deletion, budget changes or paid requests. User-run server needs restarting to load this change.

## 2026-10-05 — Detailed source walkthrough for code sharing

- Added tailored READER GUIDE comments to 25 Python modules and the React entry point, explaining ownership, inputs/outputs, call flow, operational limits and where to read next. Added inline worked examples for BM25, reciprocal-rank fusion and evidence token spans, plus clarification of state updates, cache-vs-validation boundaries and partial-answer recovery.
- Added a first-reader route and object/window/anchor/evidence glossary to coach/README.md. Comments explain the existing implementation, including its limitations; no architecture, schema, model prompt or runtime logic changed.
- Verified Python AST and executable-token equivalence during edits, and React syntax with the existing compiler. No new tests, paid requests, generated-asset changes, dependency changes or server restart were needed for these documentation-only edits.
