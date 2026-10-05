# Review before further ingestion

Scope: five actual post-refactor answers across two current local sessions (four turns plus one fresh-chat question), cached model output, server logs, source objects and a deterministic retrieval replay. Read-only review: no production code, prompts, labels, retrieval policy or ingestion changes; no new paid model calls. In-memory session snapshots and replay trace saved in ignored `.data/review_2026-10-02/` before any server restart.

## Summary

All five requests returned HTTP 200; four answers were marked insufficient, one grounded. Three optional diagrams were omitted with notices. The previously reported status/diagram conflict no longer crashes the app. This small, topic-specific sample is not a general quality estimate.

More source coverage will help eventually, but immediate weaknesses include a confirmed conversation-query bug, reversed follow-up suggestions, weak selected evidence and overly rigid answer-level sufficiency handling. Fix app behavior before interpreting ingestion as the solution.

## Prioritized findings

### 1. Follow-up suggestions reverse speaker roles — high priority

The model offers `Can you provide the SUM step or error message where you want to enter the configuration manually?` and `Do you want the Maintenance Planner explained specifically in relation to SAP system upgrades?`. Both strings then appear verbatim as user messages. UI directly submits `followups` strings as learner requests. The assistant responds “Yes” to its own offered clarification; another answer drifts to SLICENSE instead of explaining Stack XML.

Fix proposal: separate learner-clickable next questions (e.g. “Explain Maintenance Planner's role in an upgrade”) from assistant clarification questions requiring learner input. Do not render the latter as one-click user questions. Prompt and contract should encode the distinction; test the observed two strings. Entry points: prompts.py and web/src/main.jsx follow-up buttons.

### 2. Short-message context prefix contaminates a topic change — high priority, reproduced

`retrieval.py` prefixes every message shorter than ten words with the last user message, unless an element is selected. For `okay so what does a maintenance planner do`, this prepended the earlier SUM/manual-configuration error question. Replay exactly reproduces the observed five evidence IDs: figure 9717..., level paragraph 59f6..., add-on paragraph d758..., figure 54d9..., minimum-level paragraph 029e.... The answer consequently explains target levels rather than the tool.

The bare question selects different passages. This is an application conversation-scoping defect, not evidence that LangGraph forgot the conversation. Fix proposal: distinguish self-contained questions from referential follow-ups; explicit topic/entity questions should not automatically inherit the previous query. Selected diagram context also needs explicit scope/clear behavior. Keep frozen Hybrid algorithms unchanged; evaluate adapter changes with these actual conversations.

### 3. Missing selected evidence is not always missing ingested data — high priority

The fresh question `What does Maintenance Planner do?` retrieves only 160 tokens: “should be used in any scenario”, a tasks introduction, XML-generation requirements, Figure 36 caption, and heading/page-number text. The model correctly lacks the task list, but this produces an unhelpful beginner answer.

The relevant source object `adm328-v23:paragraph:8bb44240ea30` (“Use the Maintenance Planner to calculate the needed files.”) is already indexed, yet not in that context. Figure 36 is represented by its caption, not understood image content. A caption does not establish the figure's technical details.

The app uses frozen R1 source expansion, top five, on the expanded-only dataset (113 pages). It does NOT currently use the previously tested Cohere/NVIDIA rerank, graph or decomposition variants; the fresh 109-page index is not included. Decide the production adapter explicitly before assuming the benchmark's strongest scores apply to the running chatbot. This review does not reopen retrieval development or ingest more material.

### 4. Whole-answer insufficiency suppresses useful partial teaching — medium/high priority

Answers repeatedly lead with “The supplied evidence…” and end with missing-information disclaimers. Three answers include useful supported statements but lose their entire optional diagram because status is insufficient. The model also repeatedly outputs a diagram despite instructions to set it null, now safely caught by normalization.

Proposal: supported explanation first, then a concise statement of the specific missing claim. Distinguish fully supported / partially supported / unavailable at answer level, while retaining claim-level citations. Permit a diagram only of supported content, clearly scoped, rather than enabling an unsupported relationship. Do not solve this by letting the model invent SAP facts.

### 5. Citation and diagram semantics need stronger product checks — medium priority

Raw canonical IDs appear inside paragraph text AND again as source chips. Keep IDs in structured citation fields and readable document/page chips; remove them from learner-facing prose. Several limitation statements cite figure captions, which establish location/title rather than technical content. Existing validation checks ID membership, not factual entailment.

The surviving diagram uses `required with` on two separate edges to XML, which is ambiguous when read without the source sentence's joint requirement. Render precise relation labels and explanations that preserve qualifications. No visual layout judgment is claimed from this API-only review.

## Suggested next sequence

1. Fix suggestion speaker roles and topic/follow-up scoping, with saved conversations as regressions.
2. Improve partial-answer presentation and citation formatting without relaxing factual grounding.
3. Explicitly choose which already-evaluated retrieval pipeline the app should consume; this need not mean inventing another algorithm. Any change remains subject to the user's retrieval freeze.
4. Replay these questions and a few topic switches/selected-element follow-ups; inspect answer usefulness and sources, not just HTTP status.
5. Then ingest additional chapters targeted at genuinely missing concepts (e.g. Stack XML contents/constraints and SUM usage), with figure-content work treated separately. Repeating the current caption-only approach across more PDFs will not teach from their diagrams.

No code fixes are claimed by this report. Current runtime remains running with its in-memory sessions intact.
