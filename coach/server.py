"""HTTP routes for the local learning app. Conversation state lives in LangGraph."""

# READER GUIDE
# HTTP boundary: start here when tracing a browser request.
# POST /api/sessions creates a conversation; POST /api/sessions/{id}/chat
# resolves a diagram selection and invokes ConversationGraph. The graph returns
# one completed turn containing both the learner's question and the answer.
# This module owns HTTP status codes, concurrency control, PDF routes and serving
# the React build. It does not decide which SAP passages are relevant.
# For the next layer, read graph.py, then service.py. A 502 from this server can
# mean local answer validation failed, not necessarily that the provider was down.

import json
import logging
import threading
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from .errors import CoachError
from .graph import ConversationGraph
from .service import TeachingService
from .settings import DATASET_DIR, FRONTEND_DIR, MODEL_CONFIG, DOCUMENTS_DIR, STATE_DIR

logger = logging.getLogger("sap_coach")


# The browser sends text and optional diagram IDs. Reject unexpected fields at the HTTP boundary.
class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1200)
    diagram: bool = False
    artifact_id: str | None = None
    element_id: str | None = None


def find_selection(turns, artifact_id, element_id):
    """Resolve IDs only from this conversation's server-owned diagrams."""
    if not artifact_id and not element_id:
        return None
    for turn in turns:
        diagram = turn["answer"].get("diagram")
        if diagram and diagram["artifact_id"] == artifact_id:
            for element in diagram["nodes"] + diagram["edges"]:
                if element["id"] == element_id:
                    return element
    raise HTTPException(
        422, "The selected element does not belong to this conversation."
    )


# Keeping app construction in a function lets offline tests supply a fake teaching service.
def create_app(service=None, state=STATE_DIR):
    state.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="SAP Learning Coach")
    conversations = ConversationGraph(service or TeachingService(state))
    app.state.conversations = conversations
    # One worker/active generation protects the local model and reservation ledger.
    generation_lock = threading.Lock()

    def get_turns(thread_id):
        try:
            return conversations.turns(thread_id)
        except KeyError:
            raise HTTPException(
                404, "Conversation not found. Memory resets when the server restarts."
            ) from None

    # Report configuration only: this endpoint does not call the model providers or warm up retrieval.
    @app.get("/api/health")
    def health():
        return {
            "status": "ready",
            "model": MODEL_CONFIG["model"],
            "memory": "LangGraph InMemorySaver; resets on restart",
            "retrieval": "R1 + NVIDIA VL rerank · top 10 · expanded chapters",
        }

    # A session ID identifies a LangGraph conversation; it is not a user login or authentication token.
    @app.post("/api/sessions")
    def new_session():
        return {"id": conversations.create(), "messages": []}

    @app.get("/api/sessions/{thread_id}")
    def history(thread_id: str):
        return {"id": thread_id, "messages": get_turns(thread_id)}

    @app.post("/api/sessions/{thread_id}/chat")
    def chat(thread_id: str, request: ChatInput):
        if not request.message.strip():
            raise HTTPException(422, "Enter a question.")
        # Reject overlapping chat requests rather than queueing paid calls against the same local ledger.
        if not generation_lock.acquire(blocking=False):
            raise HTTPException(
                409, "Another answer is being prepared. Please try again shortly."
            )
        try:
            turns = get_turns(thread_id)
            # Look up the selected element on the server instead of trusting source text supplied by the browser.
            selection = find_selection(turns, request.artifact_id, request.element_id)
            try:
                # Hand the request to the full intent → retrieval → answer workflow; return its completed turn.
                return conversations.invoke(
                    thread_id, request.message, selection, request.diagram
                )
            # Known failures carry a safe user message and status; log an incident ID without secrets or payloads.
            except CoachError as error:
                incident = uuid.uuid4().hex[:10]
                logger.error(
                    "Chat %s: code=%s cause=%s",
                    incident,
                    error.code,
                    type(error.__cause__).__name__,
                )
                return JSONResponse(
                    status_code=error.status,
                    content={
                        "detail": str(error),
                        "code": error.code,
                        "incident": incident,
                    },
                )
            except Exception as error:
                incident = uuid.uuid4().hex[:10]
                logger.error("Chat %s: unexpected %s", incident, type(error).__name__)
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": f"An application error occurred (reference {incident}). See the server log.",
                        "code": "application_error",
                        "incident": incident,
                    },
                )
        # Always release the lock, including when selection validation or a provider call fails.
        finally:
            generation_lock.release()

    # Serve only document IDs listed in the active dataset, not arbitrary paths from the browser.
    manifest = json.loads((DATASET_DIR / "manifest.json").read_text())
    documents = {entry["key"]: entry["file"] for entry in manifest}

    @app.get("/api/documents/{document_id}")
    def document(document_id: str):
        if document_id not in documents:
            raise HTTPException(404, "Unknown document.")
        return FileResponse(
            DOCUMENTS_DIR / documents[document_id], media_type="application/pdf"
        )

    # Register the catch-all frontend last so it does not shadow the /api routes.
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="web")
    return app


app = create_app()
