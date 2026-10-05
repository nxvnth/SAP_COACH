# Handoff — SAP AI Learning Agent Project

> Current override (2 October 2026): retrieval development is frozen by user instruction. React + FastAPI + clickable SVG chat/diagram slice is implemented under coach/ and web/. See coach/README.md and the latest SESSION_LOG.md entries; older proposed-stack sections below are historical.

## 1. Project at a glance

The project is an internal SAP BASIS learning solution for LTM trainees/freshers, primarily people with CSE/ECE or similar engineering backgrounds who are new to SAP BASIS.

The original request was vague: build an AI learning platform or interactive chatbot using official SAP training material. Through discussion with the manager, the direction has evolved into a broader **SAP AI Learning Agent** with structured course delivery, grounded SAP Q&A, interactive visual explanation, voice narration, and selected hands-on SAP system interaction.

The manager does **not** want the solution framed mainly as a "PoC". In presentations, use language such as **SAP AI Learning Agent**, **Solution Overview**, **Architecture**, **Agent Orchestration**, **Knowledge Layer**, etc. The current demo is presentation-led (PowerPoint with diagrams/deliverables), not a live application demo.

## 2. Business / presentation goals

The solution has two goals:

1. Improve the learning experience for SAP BASIS freshers/trainees.
2. Give the SAP BASIS BU a credible, technically serious GenAI / agent-based initiative that can be showcased internally.

The manager is comfortable with a simple story but expects **stronger technical terminology** because the audience is SAP technical people.

The main presentation should remain high-level enough for a SAP audience. Deep retrieval details such as BM25/vector routing, candidate enrichment and reranking should be appendix/optional slides.

## 3. Core learner experience

Learner logs in and gets two main choices:

- **Continue Learning**
- **Start Chat**

### Chat experience

The learner-facing Main AI Agent should:

- answer SAP questions from approved sources,
- be beginner-friendly by default but capable of deep technical explanation,
- retain conversational context,
- identify and address apparent confusion/misconceptions when the learner expresses them,
- use analogies when useful,
- provide mandatory source citations,
- handle unsupported questions transparently instead of hallucinating,
- invoke interactive diagrams when useful,
- allow the learner to click/select/circle part of a diagram and ask about that specific component/relationship,
- retrieve SAP Notes / KBAs on demand for situational or highly specific questions.

### Course experience

The course is not intended to replace trainers. It should augment training.

Current concept:

- structured beginner-friendly content,
- diagrams / visual explanation,
- optional GUI screenshots or recordings,
- knowledge checks / quizzes,
- AI coach available alongside the course,
- selectable text / technical terms / diagram elements can be sent to the AI agent as context,
- voice narration is required by the manager, but the exact narration UX is **not fully decided yet**.

Important voice principle discussed: do not assume raw text-to-speech over the whole document is valuable. A possible future model is teacher-style narration of a lesson, but this is intentionally not frozen yet.

## 4. Course Builder Agent

There is a separate **Course Builder Agent** for admin-driven course creation.

Current flow:

1. Admin enters a topic.
2. Course Builder Agent retrieves broad, grounded SAP context using the same SAP Data Tool as the learner agent.
3. Agent plans the module structure.
4. It generates a structured module draft.
5. It may invoke the Interactive Diagram Tool where useful.
6. Admin performs technical review.
7. Admin either approves or sends revision comments.
8. The current draft + admin comments are returned to the Course Builder Agent for targeted revision.
9. Approved module is finalized and published/rendered in the learner UI.

Do **not** split this into planner/writer/quiz-generator agents unless a concrete failure justifies that complexity.

The user follows a strict architecture philosophy:

> **What failure am I solving by adding this component?**

Use this principle in all future design discussions.

## 5. SAP system integration

The manager explicitly said SAP system integration is **good and a must** for the broader solution.

Access to an SAP training system may not yet be available, so the exact implementation remains TBD.

The system integration should be constrained to selected learning activities such as:

- running or viewing permitted TCodes,
- TMS-related exercises,
- inspecting configuration/system state,
- reading or changing explicitly permitted parameters,
- validating completion of controlled exercises.

Do not turn the project into a full SAP training lab / OS-level automation platform. Broad OS-level operations, filesystem work, SUM directories, kernel operations, full upgrade execution, etc. are outside the initial solution boundary.

Technical controls to preserve in the design:

- dedicated training role/user,
- least privilege,
- whitelisted operations,
- read-only where possible,
- exercise-level validation,
- logging/auditing,
- no unrestricted OS-level administration.

## 6. Knowledge sources

### Indexed/static learning sources

The system now needs to support more than TADMs.

Available / expected sources include:

- ADM328 — SAP S/4HANA Conversion and SAP System Upgrade,
- additional TADMs over time,
- SAP HANA Administration Guide / SAP Help material,
- other approved SAP technical documents.

The HANA Administration Guide is especially important for beginners because it provides foundational HANA administration material and has a structure very different from a TADM.

### SAP Notes / KBAs

SAP Notes should be treated as **situational, on-demand external knowledge**, not necessarily pre-ingested into the same static knowledge store.

Current idea:

- expose SAP Notes / KBA retrieval as a tool,
- candidate implementation is an existing MCP server that authenticates using SAP credentials / SAP Passport and uses Playwright to retrieve Note/KBA content,
- keep the architecture coupled to a generic **SAP Notes Retrieval Tool**, not to that one specific MCP implementation.

## 7. Document ingestion observations

### TADM observations

The user manually inspected TADMs and found:

1. Each unit has unit objectives on the first page.
2. Unit objectives often restate lesson names as action statements.
3. A concept may be introduced before the unit/lesson dedicated to teaching it. Example: Maintenance Planner is described before the dedicated Maintenance Planner unit.
4. TADMs contain many diagrams as embedded images; useful visual knowledge may require image processing.
5. Each lesson has a learning assessment; questions may be repeated, with one copy containing answers.

Implications:

- preserve pedagogical structure,
- distinguish `mentioned_in`, `defined_in`, `taught_in`, etc.,
- figures should be first-class content objects,
- assessments should be extracted/deduplicated and linked to lessons,
- objectives can enrich lesson/unit metadata and embeddings.

### SAP Help / HANA guide observations

The HANA Administration Guide has:

- deep chapter/section/subsection hierarchy,
- long technical explanations,
- procedures,
- SQL/code blocks,
- large technical tables,
- diagrams/architecture figures,
- Related Information links,
- SAP Note references,
- configuration syntax,
- system limits/reference data.

Therefore the ingestion design is now:

> **Common ingestion framework + document-type-specific parsers/profiles → shared canonical SAP knowledge model.**

Do not build one generic PDF parser that flattens everything into fixed-size chunks.

## 8. Knowledge architecture

Current high-level ingestion architecture:

`SAP documents → document-specific ingestion + parsing → document tree + knowledge graph → SAP knowledge store + vector DB + BM25 index`

### Separate two kinds of structure

**Document / pedagogical structure**

- TADM → Unit → Lesson → Section → Content Object
- HANA Guide → Chapter → Section → Subsection → Content Object
- Procedure → ordered steps

This answers: *Where is this taught? What comes before/after? What is the complete procedure?*

**Domain knowledge relationships**

Examples:

- `SM37 --monitors--> Background Job`
- `Background Work Process --executes--> Background Job`
- `Procedure X --uses--> Transaction Y`
- `Concept A --prerequisite_of--> Concept B`
- `Concept C --taught_in--> Lesson D`

This answers: *How do SAP concepts/components relate?*

### Canonical content object idea

Objects/nodes should have stable IDs and enough semantic content to serve as retrieval anchors, for example:

- id,
- type,
- title,
- short source-grounded summary,
- source document/location,
- parent/child relationships,
- linked content objects,
- related entities,
- metadata.

Important rule discussed:

> **Nodes should be sufficient for orientation; linked content objects should be sufficient for explanation.**

## 9. Retrieval architecture

The retrieval design is **not fully frozen**. It is being validated experimentally.

The user wants to implement and compare:

1. **Parallel hybrid retrieval**
2. **Routed hybrid retrieval**

with validation queries and measurable retrieval quality.

### Parallel hybrid baseline

Current planned flow:

`Query → light preprocessing → BM25 + vector + structured knowledge lookup in parallel → normalize hits → merge by canonical ID → candidate anchors → knowledge-store enrichment → rerank → context builder → Main Agent`

Principles:

- BM25 solves exact SAP identifiers/terminology: TCodes, parameters, error/status strings, program names.
- Vector search solves semantic/natural-language phrasing.
- Structured knowledge lookup provides document structure and concept relationships.
- Enrichment should primarily expand candidate anchors through the knowledge store; do not blindly rerun all searches during enrichment.
- Enrichment should be controlled (e.g. 1-hop, relevant parent/child context, complete ordered procedure when needed), not unbounded graph traversal.
- Raw BM25 and vector scores are not directly comparable; normalize/merge before ranking.
- Stable canonical IDs are important so the same underlying object retrieved by multiple channels can be merged.

### Routed retrieval

Do not assume a router is useful until measured.

If implemented, routing should produce a **retrieval plan**, not simply select one store. Example outputs might specify:

- intent,
- detected SAP entities,
- BM25 yes/no or weight,
- vector yes/no or weight,
- structured lookup yes/no,
- procedure expansion,
- pedagogical expansion.

Possible deterministic + model-assisted routing is under discussion.

### Evaluation plan

Use the same validation queries for all strategies. Consider three configurations:

- R0 — simple vector baseline,
- R1 — parallel hybrid,
- R2 — routed hybrid.

Measure retrieval separately from final answer quality:

- correct source/object in Top-K,
- rank of first correct result / MRR-style metric,
- context precision / noise,
- context completeness,
- procedure ordering correctness,
- relationship completeness,
- latency,
- context tokens,
- final grounding/citation correctness.

Do not let a strong LLM hide poor retrieval.

## 10. Main AI Agent architecture

The initial solution deliberately uses **one learner-facing Main AI Agent** rather than many agents.

Logical responsibilities remain separate, but are not necessarily separate services/agents:

1. Query understanding / intent recognition
2. Knowledge retrieval / context assembly
3. Reasoning / teaching orchestration
4. Response formulation
5. Diagram generation / visual tool invocation

The Main Agent should not own retrieval internals. The application/tool layer owns retrieval; the agent owns synthesis and teaching.

Current tool registry:

- **SAP Data Tool** — retrieves grounded context from indexed approved SAP documents,
- **SAP Notes Retrieval Tool** — on-demand SAP Note/KBA lookup,
- **Interactive Diagram Tool** — generates structured visual artifacts and supports element-level interaction,
- future **SAP System Integration Tool** — controlled training operations.

Conversation/course/selected-artifact context is also available to the agent.

## 11. Interactive diagrams

Target behavior:

- agent decides when a visual is useful,
- diagram is generated from grounded SAP context,
- diagram should ideally have structured semantic nodes/edges rather than being only a flat image,
- learner can click/select/circle components/relationships,
- UI resolves the selection back to semantic IDs,
- selected IDs become new context for the Main Agent.

Candidate implementation: **draw.io MCP + a custom diagram/teaching skill**, but this is not yet validated.

Important distinction:

- draw.io/MCP may solve diagram creation/layout,
- the app still needs semantic selection and interaction logic.

Do not make draw.io the source of truth if it cannot preserve stable semantic identifiers.

## 12. Voice narration

Manager requested a voice feature to read out the course.

Current state:

- voice narration is included as a capability,
- exact UX is intentionally undecided,
- do not reduce it to “accessibility” or assume reading every paragraph aloud is useful,
- possible future direction: lesson-level teacher-style narration that guides attention across visual material,
- for now, present it as **voice-enabled lesson narration / TTS output channel** without overcommitting.

## 13. Presentation feedback / current deck

Manager feedback on the earlier deck:

- did not like the solution being framed around “PoC”,
- wanted the name to emphasize an agent / technical solution,
- accepted the simple visual style but wanted stronger technical terminology,
- requested Slide 7/course builder to explicitly include the admin steps,
- requested extra slides showing the user journey from start to finish,
- old slides 8–10 (deliverables / roadmap / retrieval) should be optional / extra rather than core story.

The revised deck is:

`SAP_AI_Learning_Agent_Solution_Overview.pptx`

Main deck structure:

1. SAP AI Learning Agent — Solution Overview
2. Solution context & technical objectives
3. End-to-end learner journey
4. Learning experience — course + AI agent
5. High-level technical architecture
6. SAP knowledge ingestion architecture
7. Agent orchestration & tool registry
8. Course generation — admin workflow
9. Controlled SAP system integration
10. Technical data flow — learner query
11. Appendix divider
12. Supporting deliverables
13. Phased implementation direction
14. Retrieval architecture deep dive

## 14. Current diagrams / terminology

The latest presentation-level terminology should use:

- **SAP AI Learning Agent**
- **SAP Data Tool** rather than TADM Data Tool
- **SAP Knowledge Store** rather than TADM Knowledge Store
- **SAP Notes Retrieval Tool** rather than generic MCP Tool
- **Document-specific ingestion + parsing**
- **Tool Registry**
- **Course Builder Agent**
- **Interactive Diagram Tool**
- **Conversational History and Artifacts**

Some older embedded diagram screenshots still contain earlier labels such as TADM Data Tool. Treat these as logical diagrams and update/recreate them later if the deck needs pixel-perfect terminology consistency.

## 15. Important open decisions

Do not silently decide these without discussion:

- exact technology stack,
- exact frontend/backend frameworks,
- exact agent/orchestration framework,
- exact LLM/model and SAP AI Core configuration,
- vector database,
- BM25 implementation,
- graph database vs relational graph representation,
- exact parsing tooling,
- diagram technology after spike/validation,
- conversation/artifact storage,
- course content storage,
- SAP system integration mechanism,
- exact SAP hands-on exercise,
- voice narration UX,
- exact source-citation schema,
- whether/how figures/tables/code are transformed into canonical objects,
- whether a router measurably improves retrieval.

## 16. How the assistant should work with the user

This project is also a learning exercise for the user. Do not simply design everything for them.

The user explicitly wants an FDE-like thinking coach who:

- challenges assumptions,
- points out missing decisions,
- asks the user to reason through tradeoffs,
- provides examples when they are out of depth,
- does not overengineer,
- does not add components without a concrete failure/requirement,
- helps convert abstract architecture into measurable tests,
- calls out when a decision is premature,
- separates requirements from implementation choices,
- preserves a list of open decisions and assumptions.

When the user asks to draft a spec/HLD, first ensure key decisions have actually been discussed. Mark unresolved items as TBD instead of inventing them.


### Latest app override — standalone LangGraph refactor (2 October 2026)

Active app code/frontend/runtime assets now live entirely under coach/. Run `python run.py` from that directory. LangGraph InMemorySaver replaces active SQLite chat memory; restart clears threads, and old SQLite records remain archived. Answer model is AIcredits openai/gpt-5.6-luna. See coach/README.md for code map, local setup, memory limits and the fixed insufficient-answer/diagram error. Retrieval remains frozen.
