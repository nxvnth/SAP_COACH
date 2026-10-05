"""Thread memory and orchestration using LangGraph's in-process checkpointer.

START -> understand -> retrieve -> generate -> validate -> commit -> END
Only commit adds a completed turn. Failed generations never become chat history.
"""

import uuid
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from .settings import HISTORY_CHARACTER_LIMIT, HISTORY_MESSAGE_LIMIT


# State fields are the shared worksheet for graph nodes. Each node returns only the fields it changes.
class ChatState(TypedDict, total=False):
    intent: dict
    turns: list[dict]
    message: str
    selection: dict | None
    want_diagram: bool
    history: list[dict]
    retrieved: dict
    raw_answer: dict
    answer: dict
    last_turn: dict


def history_window(turns):
    """Bound model input, while the full turn history remains in thread memory."""
    messages = []
    for turn in turns:
        messages.append({"role": "user", "text": turn["question"]})
        messages.append(
            {
                "role": "assistant",
                "text": "\n".join(block["text"] for block in turn["answer"]["blocks"]),
            }
        )
    # Walk backward to keep the newest messages that fit, then restore their conversational order.
    chosen = []
    remaining = HISTORY_CHARACTER_LIMIT
    for message in reversed(messages[-HISTORY_MESSAGE_LIMIT:]):
        if len(message["text"]) > remaining:
            break
        chosen.append(message)
        remaining -= len(message["text"])
    return list(reversed(chosen))


class ConversationGraph:
    def __init__(self, service):
        self.service = service
        # The checkpointer holds state in this process; restarting the server loses these threads.
        self.checkpointer = InMemorySaver()
        builder = StateGraph(ChatState)
        builder.add_node("understand", self.understand)
        builder.add_node("clarify", self.clarify)
        builder.add_node("retrieve", self.retrieve)
        builder.add_node("generate", self.generate)
        builder.add_node("validate", self.validate)
        builder.add_node("commit", self.commit)
        for source, target in [
            (START, "understand"),
            ("clarify", "commit"),
            ("retrieve", "generate"),
            ("generate", "validate"),
            ("validate", "commit"),
            ("commit", END),
        ]:
            builder.add_edge(source, target)
        # Unclear references take a clarification branch, avoiding retrieval and answer-generation calls.
        builder.add_conditional_edges(
            "understand",
            lambda state: (
                "clarify"
                if state["intent"]["relationship"] == "ambiguous"
                else "retrieve"
            ),
        )
        self.graph = builder.compile(checkpointer=self.checkpointer)

    @staticmethod
    # LangGraph uses this thread_id to keep one conversation separate from another.
    def config(thread_id):
        return {"configurable": {"thread_id": thread_id}}

    def create(self):
        thread_id = str(uuid.uuid4())
        self.graph.update_state(self.config(thread_id), {"turns": []})
        return thread_id

    def turns(self, thread_id):
        state = self.graph.get_state(self.config(thread_id))
        if not state.values:
            raise KeyError("Conversation not found")
        return state.values.get("turns", [])

    def invoke(self, thread_id, message, selection=None, want_diagram=False):
        self.turns(thread_id)
        state = self.graph.invoke(
            {"message": message, "selection": selection, "want_diagram": want_diagram},
            self.config(thread_id),
        )
        return state["last_turn"]

    def understand(self, state):
        history = history_window(state.get("turns", []))
        intent = self.service.understand(state["message"], history, state["selection"])
        return {"history": history, "intent": intent}

    # A clarification is saved as a normal conversational turn, but asserts no sourced SAP facts.
    def clarify(self, state):
        return {
            "answer": dict(
                status="insufficient",
                blocks=[dict(text=state["intent"]["clarification"], source_ids=[])],
                diagram=None,
                followups=[],
                clarification=None,
                sources=[],
                notices=[],
                retrieval_tokens=0,
                query_intent=state["intent"],
            )
        }

    # The intent node has already rewritten references. Passing old history here would contaminate search.
    def retrieve(self, state):
        selection = state["selection"] if state["intent"]["use_selection"] else None
        retrieved = self.service.retrieve(
            state["intent"]["standalone_question"], [], selection
        )
        return {"retrieved": retrieved}

    # For a new standalone topic, also drop history from the answer prompt—not just from search.
    def generate(self, state):
        raw = self.service.generate(
            state["intent"]["standalone_question"],
            [] if state["intent"]["relationship"] == "standalone" else state["history"],
            state["selection"] if state["intent"]["use_selection"] else None,
            state["want_diagram"],
            state["retrieved"]["evidence"],
        )
        return {"raw_answer": raw}

    def validate(self, state):
        answer = self.service.validate(state["raw_answer"], state["retrieved"])
        answer["query_intent"] = state["intent"]
        return {"answer": answer}

    # Only this node appends a visible turn. Failed retrieval/generation/validation never reaches it.
    def commit(self, state):
        turn = {
            "id": str(uuid.uuid4()),
            "question": state["message"],
            "answer": state["answer"],
        }
        return {"turns": state.get("turns", []) + [turn], "last_turn": turn}
