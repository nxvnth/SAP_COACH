"""Small paid regression replay. Reuses a fixed cache and a six-call/$0.08 cap."""

# READER GUIDE
# Targeted paid replay of the topic-contamination regression.
# The sequence moves from Stack XML to Maintenance Planner, then asks about
# "its" role in upgrades. Assertions check that the new topic is independent
# and the follow-up resolves to the recent subject.
# The fixed test ledger is intentionally reused across runs. --resume-followup
# uses saved first turns to avoid regenerating them; it is a diagnostic replay,
# not the normal user-facing conversation-resume feature.

import json
import sys
from .contracts import normalize_answer
from .graph import ConversationGraph
from .provider import Client
from .service import TeachingService
from .settings import STATE_DIR, MODEL_CONFIG


# Replay a short real conversation against the providers using the fixed, capped regression ledger.
def main():
    directory = STATE_DIR / "quality_check"
    directory.mkdir(exist_ok=True)
    config = dict(MODEL_CONFIG, max_calls=6, budget_usd=0.08)
    service = TeachingService(directory, client=Client(directory / "api", config))
    graph = ConversationGraph(service)
    thread = graph.create()
    questions = [
        "What is the purpose of the stack XML file?",
        "Okay so what does Maintenance Planner do?",
        "Explain its role in upgrades.",
    ]
    selection = None
    start = 0
    if "--resume-followup" in sys.argv:
        previous = json.loads((directory / "answers.json").read_text())
        (directory / "initial_answers.json").write_text(json.dumps(previous, indent=2))
        completed = previous[:2]
        # Reapply display validation without another provider request.
        for turn in completed:
            answer = turn["answer"]
            raw = {
                key: answer[key]
                for key in ("status", "blocks", "diagram", "followups", "clarification")
            }
            raw["diagram"] = None
            cleaned = normalize_answer(raw, {s["id"]: s for s in answer["sources"]})
            answer["blocks"] = cleaned["blocks"]
        graph.graph.update_state(graph.config(thread), {"turns": completed})
        if completed[-1]["answer"]["diagram"]:
            selection = completed[-1]["answer"]["diagram"]["nodes"][0]
        start = 2
    for question in questions[start:]:
        turn = graph.invoke(thread, question, selection, True)
        answer = turn["answer"]
        (directory / "answers.json").write_text(
            json.dumps(graph.turns(thread), indent=2)
        )
        print(
            json.dumps(
                {
                    "question": question,
                    "status": answer["status"],
                    "intent": answer["query_intent"],
                    "query": answer.get("retrieval_query"),
                    "evidence_count": len(answer["sources"]),
                    "text": [block["text"] for block in answer["blocks"]],
                    "followups": answer["followups"],
                }
            ),
            flush=True,
        )
        if answer["diagram"]:
            selection = answer["diagram"]["nodes"][0]
    answers = graph.turns(thread)
    assert answers[1]["answer"]["query_intent"]["relationship"] == "standalone"
    assert not answers[1]["answer"]["query_intent"]["use_selection"]
    assert "Maintenance Planner" in answers[2]["answer"]["retrieval_query"]


if __name__ == "__main__":
    main()
