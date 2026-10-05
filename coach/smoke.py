"""Bounded live check through the LangGraph pipeline, using the standalone app."""

import json
from .graph import ConversationGraph
from .service import TeachingService
from .settings import APP_DIR


# This is a live integration check with paid provider calls and a separate cache/usage directory.
def main():
    directory = APP_DIR / ".smoke_langgraph"
    directory.mkdir(exist_ok=True)
    graph = ConversationGraph(TeachingService(directory))
    thread_id = graph.create()
    first = graph.invoke(
        thread_id, "What is the purpose of the stack XML file?", want_diagram=True
    )
    diagram = first["answer"]["diagram"]
    selection = diagram["nodes"][0] if diagram else None
    second = graph.invoke(
        thread_id, "Okay then once I generate it, what happens next?", selection, True
    )
    assert len(graph.turns(thread_id)) == 2
    assert first["answer"]["blocks"] and second["answer"]["blocks"]
    (directory / "answers.json").write_text(
        json.dumps(graph.turns(thread_id), indent=2)
    )
    print(
        {
            "first": first["answer"]["status"],
            "followup": second["answer"]["status"],
            "notices": second["answer"]["notices"],
            "turns": 2,
        }
    )


if __name__ == "__main__":
    main()
