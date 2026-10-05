"""Retrieve evidence, generate an answer, and validate it: LangGraph calls these steps."""

# READER GUIDE
# Application operations called by the workflow nodes.
# TeachingService coordinates three separate concerns: query understanding,
# source retrieval, and answer generation/validation. The same answer-model
# client is used for intent and teaching, but each has a different prompt/schema.
# The retriever returns original passages; the generator turns those passages
# into an explanation and optional diagram; contracts.py checks the result.
# Constructor injection lets tests supply fake providers/retrievers. To promote
# a new retrieval experiment, preserve the retrieve() return contract instead
# of changing the server or the conversation graph.

import json
import uuid
from .contracts import Answer, QueryIntent, normalize_answer, validate_intent
from .errors import CoachError, provider_error
from .prompts import SYSTEM, INTENT_SYSTEM
from .provider import Client
from .retrieval import Retriever
from .settings import MODEL_CONFIG, STATE_DIR


# This is the bridge between graph orchestration, the replaceable retriever, and the answer API.
class TeachingService:
    def __init__(self, state_dir=STATE_DIR, retriever=None, client=None):
        self.state_dir = state_dir
        self.retriever = retriever or Retriever(state_dir)
        self.client = client

    # Initialize the API client lazily; fetch model availability/pricing when local metadata does not match.
    def ensure_client(self):
        if self.client is None:
            self.client = Client(self.state_dir / "api", MODEL_CONFIG)
        metadata_path = self.state_dir / "api/provider_model.json"
        metadata = (
            json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        )
        if metadata.get("model") != MODEL_CONFIG["model"]:
            self.client.preflight()

    def understand(self, message, history, selection):
        # With no conversational references to resolve, skip the extra intent model call.
        if not history and not selection:
            return dict(
                relationship="standalone",
                standalone_question=message,
                use_selection=False,
                clarification="",
            )
        try:
            self.ensure_client()
            raw = self.client.call(
                "intent",
                INTENT_SYSTEM,
                dict(message=message, history=history, selected_element=selection),
                QueryIntent.model_json_schema(),
                700,
            )
            # Check the structured rewrite before using it to select evidence.
            return validate_intent(raw, message, selection)
        except ValueError as error:
            raise CoachError(
                "invalid_intent",
                "The question could not be resolved safely. Please name the topic or component explicitly.",
            ) from error
        except RuntimeError as error:
            raise provider_error(error) from error

    # This small interface is the replacement point for a retrieval implementation promoted from experiments.
    def retrieve(self, message, history, selection):
        return self.retriever.retrieve(message, history, selection)

    def generate(self, message, history, selection, want_diagram, evidence):
        # Without any retrieved sources, return an explicit gap instead of asking the model to invent an answer.
        if not evidence:
            return {
                "status": "insufficient",
                "blocks": [
                    {
                        "text": "I could not find source evidence for that question.",
                        "source_ids": [],
                    }
                ],
                "diagram": None,
                "followups": [],
            }
        try:
            self.ensure_client()
            # Keep evidence and conversational context in separate fields: history is not a factual source.
            payload = {
                "question": message,
                "history": history,
                "selected_element": selection,
                "request_diagram": want_diagram,
                "evidence": list(evidence.values()),
            }
            return self.client.call(
                "teaching",
                SYSTEM,
                payload,
                Answer.model_json_schema(),
                MODEL_CONFIG["max_output_tokens"],
            )
        except RuntimeError as error:
            raise provider_error(error) from error

    def validate(self, raw, retrieved):
        try:
            answer = normalize_answer(raw, retrieved["evidence"])
        except ValueError as error:
            raise CoachError(
                "invalid_answer",
                "The generated answer contained invalid citations or fields. It was not added to the conversation.",
            ) from error
        # Give each accepted diagram a unique artifact ID so later clicks refer to the correct saved diagram.
        if answer["diagram"]:
            answer["diagram"]["artifact_id"] = str(uuid.uuid4())
        # Attach source excerpts and a retrieval trace for citation rendering and debugging.
        answer.update(
            sources=list(retrieved["evidence"].values()),
            retrieval_tokens=retrieved["retrieval_tokens"],
            selected_source_ids=retrieved["selected_source_ids"],
            retrieval_policy="R1 + NVIDIA VL rerank · top 10 · expanded chapters",
            retrieval_query=retrieved.get("query"),
            selected_anchor_ids=retrieved.get("selected_anchor_ids", []),
            model=MODEL_CONFIG["model"],
        )
        return answer
