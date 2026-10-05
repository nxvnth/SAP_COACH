"""App retrieval entry point: fused candidates, NVIDIA ranking, source context."""

# READER GUIDE
# Public entry point for the app's current retrieval implementation.
# Input: an already-resolved question, an unused compatibility history argument,
# and an optional server-verified diagram element with source_ids.
# Flow: Hybrid.search candidate pool -> NVIDIA relevance scores -> top-ten
# anchors -> bounded source expansion -> evidence dictionary for the teacher.
# An anchor is a ranked content object. One procedure anchor can expand into
# several evidence passages, so ten anchors does not mean ten final paragraphs.
# selected_anchor_ids records the ranking cutoff, not a guarantee that every
# anchor fit the context budget. retrieval_tokens measures assembled context
# before additional selected-element sources; it is not the full LLM prompt size.

from ..settings import DATASET_DIR, STATE_DIR
from .reranker import Client, body, rankings
from ..errors import CoachError


class Retriever:
    def __init__(self, state_dir=STATE_DIR):
        self.engine = None
        self.reranker = Client(state_dir / "rerank", max_calls=200)

    # Load the local model and index on first use rather than during web-server startup.
    def initialize(self):
        if self.engine is not None:
            return
        from .hybrid import Hybrid

        self.engine = Hybrid(DATASET_DIR)

    def retrieve(self, message, history, selection):
        self.initialize()
        # The LangGraph intent node has already resolved this query. Never append history here.
        query = message
        # First collect a fused candidate pool; these are candidates, not yet the final teaching evidence.
        hits, _, _, _ = self.engine.search(query)
        if not hits:
            return dict(
                query=query,
                candidate_count=0,
                selected_anchor_ids=[],
                evidence={},
                retrieval_tokens=0,
                selected_source_ids=[],
            )
        from . import vector

        # Give the reranker each candidate’s section path and source content so short fragments have context.
        documents = [
            " > ".join(
                vector.ancestors(self.engine.by[h["canonical_id"]], self.engine.by)
            )
            + "\n"
            + "\n".join(
                text
                for _, text in vector.units(
                    self.engine.by[h["canonical_id"]], self.engine.by
                )
            )
            for h in hits
        ]
        try:
            response = self.reranker.call(body(query, documents))
            ranked_items = rankings(response, len(hits))
        except (RuntimeError, ValueError, KeyError, TypeError) as error:
            raise CoachError(
                "reranker_unavailable",
                "Evidence ranking could not complete. Check NVIDIA_API_KEY and the reranking ledger; no automatic retry was made.",
            ) from error
        # Provider indices refer to the submitted candidate list; map them back to stable source objects.
        reranked = [
            dict(hits[item["index"]], rerank_score=item["logit"])
            for item in ranked_items
        ]
        # Expand the ten best anchors into original source units while applying the context token budget.
        context = self.engine.context(reranked, query, True, top_k=10)
        evidence = {
            item["id"]: {
                "id": item["id"],
                "text": item["text"],
                "source": item["source"],
            }
            for item in context["items"]
        }
        selected_ids = []
        # An explicitly relevant diagram selection contributes its source references separately from ranked context.
        if selection:
            for source_id in selection["source_ids"]:
                source = self.engine.by.get(source_id)
                if source is not None:
                    evidence[source_id] = {
                        "id": source_id,
                        "text": source["text"],
                        "source": source["source"],
                    }
                    selected_ids.append(source_id)
        # The teaching service consumes evidence, while the extra fields explain
        # how it was selected. Keep canonical IDs unchanged when swapping this
        # implementation so citation links and diagram follow-ups remain meaningful.
        return {
            "query": query,
            "candidate_count": len(hits),
            "selected_anchor_ids": [h["canonical_id"] for h in reranked[:10]],
            "rerank_latency_ms": response["_client_latency_ms"],
            "evidence": evidence,
            "retrieval_tokens": context["tokens"],
            "selected_source_ids": selected_ids,
        }
