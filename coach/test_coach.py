"""Offline regressions for output validation, thread memory and standalone runtime."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from .contracts import normalize_answer, validate_intent
from .errors import CoachError
from .graph import ConversationGraph, history_window
from .retrieval.index_store import validate_index
from .settings import DATASET_DIR, APP_DIR
from .server import create_app

BASE = {
    "status": "grounded",
    "blocks": [{"text": "Supported explanation", "source_ids": ["source1"]}],
    "followups": [],
    "diagram": {
        "title": "Example",
        "nodes": [
            {
                "id": "n1",
                "label": "Component",
                "explanation": "Explanation",
                "source_ids": ["source1"],
                "explanatory": False,
            }
        ],
        "edges": [],
    },
}


# Replace provider/retrieval work with predictable responses so graph and HTTP tests remain offline.
class FakeService:
    def __init__(self):
        self.selection = None
        self.histories = []
        self.fail = False

    def understand(self, message, history, selection):
        self.histories.append(history)
        return dict(
            relationship="selection" if selection else "standalone",
            standalone_question=message,
            use_selection=bool(selection),
            clarification="",
        )

    def retrieve(self, message, history, selection):
        self.selection = selection
        return {
            "evidence": {"source1": {}},
            "retrieval_tokens": 0,
            "selected_source_ids": [],
        }

    def generate(self, *args):
        if self.fail:
            raise CoachError("budget_exhausted", "Budget limit reached.", 429)
        return copy.deepcopy(BASE)

    def validate(self, raw, retrieved):
        answer = normalize_answer(raw, retrieved["evidence"])
        answer["diagram"]["artifact_id"] = "artifact"
        answer["sources"] = []
        return answer


# These regressions exercise conversation isolation, validation and the retrieval adapter contract.
class CoachTests(unittest.TestCase):
    def test_app_reranking_orders_anchors_with_explicit_cutoff(self):
        from unittest.mock import Mock
        from .retrieval import Retriever

        engine = Mock()
        engine.by = {
            key: dict(id=key, text=text, type="paragraph", parent_id=None)
            for key, text in [("a", "First"), ("b", "Second")]
        }
        engine.search.return_value = (
            [{"canonical_id": "a"}, {"canonical_id": "b"}],
            None,
            None,
            None,
        )

        def assemble(hits, query, expand, top_k):
            self.assertEqual(top_k, 10)
            self.assertEqual([h["canonical_id"] for h in hits], ["b", "a"])
            return {"items": [], "tokens": 0}

        engine.context.side_effect = assemble
        with tempfile.TemporaryDirectory() as directory:
            retriever = Retriever(Path(directory))
            retriever.engine = engine
            retriever.reranker = Mock()
            retriever.reranker.call.return_value = {
                "rankings": [{"index": 0, "logit": 1}, {"index": 1, "logit": 4}],
                "_client_latency_ms": 10,
            }
            result = retriever.retrieve("New topic", [{"text": "Old topic"}], None)
            self.assertEqual(result["selected_anchor_ids"], ["b", "a"])
            engine.search.assert_called_with("New topic")
            engine.context.assert_called_once()

    def test_reported_addon_answer_preserves_cited_content(self):
        raw = json.loads((Path(__file__).parent / "tests/fixtures/partial_with_uncited_gap.json").read_text())
        evidence = {source_id: {} for block in raw["blocks"] for source_id in block["source_ids"]}
        result = normalize_answer(raw, evidence)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["blocks"], raw["blocks"][:2])
        self.assertIsNotNone(result["diagram"])
        self.assertIn("uncited text was omitted", result["notices"][0])

    def test_uncited_claim_is_never_displayed_or_given_invented_citations(self):
        raw = copy.deepcopy(BASE)
        raw["blocks"].append({"text": "An unsupported technical claim", "source_ids": []})
        result = normalize_answer(raw, {"source1": {}})
        self.assertEqual(result["blocks"], BASE["blocks"])
        self.assertEqual(result["status"], "partial")
        raw["blocks"][1]["source_ids"] = ["invented"]
        with self.assertRaisesRegex(ValueError, "Unknown citation"):
            normalize_answer(raw, {"source1": {}})

    def test_partial_answer_keeps_supported_diagram(self):
        answer = copy.deepcopy(BASE)
        answer["status"] = "partial"
        self.assertIsNotNone(normalize_answer(answer, {"source1": {}})["diagram"])
        answer["blocks"][0]["source_ids"] = []
        with self.assertRaises(ValueError):
            normalize_answer(answer, {"source1": {}})

    def test_citation_cleanup_and_followup_speaker(self):
        answer = copy.deepcopy(BASE)
        source_id = "adm328-v23:paragraph:123"
        answer["diagram"] = None
        answer["blocks"] = [
            {
                "text": f"Useful facts [{source_id}] \ue200cite\ue202{source_id}\ue201",
                "source_ids": [source_id, source_id],
            }
        ]
        answer["followups"] = ["Do you want an example?", "Explain the next step"]
        result = normalize_answer(answer, {source_id: {}})
        self.assertEqual(
            result["blocks"], [{"text": "Useful facts", "source_ids": [source_id]}]
        )
        self.assertEqual(result["followups"], ["Explain the next step"])
        self.assertEqual(result["clarification"], "Do you want an example?")

    def test_intent_preserves_explicit_question(self):
        raw = dict(
            relationship="standalone",
            standalone_question="Old topic",
            use_selection=True,
            clarification="",
        )
        result = validate_intent(
            raw, "What does Maintenance Planner do?", {"label": "SUM"}
        )
        self.assertEqual(
            result["standalone_question"], "What does Maintenance Planner do?"
        )
        self.assertFalse(result["use_selection"])
        raw.update(relationship="followup", use_selection=False)
        with self.assertRaises(ValueError):
            validate_intent(raw, "Explain --nostart_tenant_db in 2.0", None)

    def test_new_topic_drops_history_and_stale_selection(self):
        from unittest.mock import Mock

        service = FakeService()
        graph = ConversationGraph(service)
        thread = graph.create()
        graph.invoke(thread, "Old question")
        service.understand = Mock(
            return_value=dict(
                relationship="standalone",
                standalone_question="New topic",
                use_selection=False,
                clarification="",
            )
        )
        service.generate = Mock(return_value=copy.deepcopy(BASE))
        graph.invoke(thread, "New topic", {"source_ids": ["old"]})
        self.assertIsNone(service.selection)
        self.assertEqual(service.generate.call_args.args[:3], ("New topic", [], None))

    def test_ambiguous_question_does_not_retrieve_or_generate(self):
        from unittest.mock import Mock

        service = FakeService()
        service.understand = Mock(
            return_value=dict(
                relationship="ambiguous",
                standalone_question="",
                use_selection=False,
                clarification="Which component?",
            )
        )
        service.retrieve = Mock(side_effect=AssertionError("Should not retrieve"))
        service.generate = Mock(side_effect=AssertionError("Should not generate"))
        graph = ConversationGraph(service)
        thread = graph.create()
        turn = graph.invoke(thread, "What about it?")
        self.assertEqual(turn["answer"]["blocks"][0]["text"], "Which component?")
        self.assertEqual(len(graph.turns(thread)), 1)

    def test_index_integrity(self):
        config = json.loads((APP_DIR / "retrieval/embedding_model.json").read_text())
        validate_index(DATASET_DIR, config)

    def test_actual_reported_followup_response(self):
        fixture = (
            Path(__file__).parent / "tests/fixtures/insufficient_with_diagram.json"
        )
        raw = json.loads(fixture.read_text())
        evidence = {
            source_id: {}
            for block in raw["blocks"]
            for source_id in block["source_ids"]
        }
        result = normalize_answer(raw, evidence)
        self.assertEqual(result["blocks"], raw["blocks"])
        self.assertIsNone(result["diagram"])
        self.assertTrue(result["notices"])

    def test_insufficient_diagram_preserves_text(self):
        answer = copy.deepcopy(BASE)
        answer["status"] = "insufficient"
        result = normalize_answer(answer, {"source1": {}})
        self.assertIsNone(result["diagram"])
        self.assertEqual(result["blocks"], answer["blocks"])
        self.assertTrue(result["notices"])

    def test_bad_diagram_does_not_discard_answer(self):
        answer = copy.deepcopy(BASE)
        answer["diagram"]["nodes"][0]["source_ids"] = ["invented"]
        result = normalize_answer(answer, {"source1": {}})
        self.assertIsNone(result["diagram"])
        self.assertEqual(result["status"], "grounded")

    def test_bad_text_citation_still_rejected(self):
        with self.assertRaises(ValueError):
            normalize_answer(BASE, {})

    def test_thread_memory_and_failed_turn(self):
        service = FakeService()
        graph = ConversationGraph(service)
        first, second = graph.create(), graph.create()
        graph.invoke(first, "First question")
        graph.invoke(first, "Follow up")
        self.assertEqual(len(service.histories[-1]), 2)
        self.assertEqual(graph.turns(second), [])
        service.fail = True
        with self.assertRaises(CoachError):
            graph.invoke(first, "Failed question")
        self.assertEqual(len(graph.turns(first)), 2)
        service.fail = False
        graph.invoke(first, "New question")
        self.assertEqual(len(graph.turns(first)), 3)
        self.assertNotIn("Failed question", str(service.histories[-1]))
        with self.assertRaises(KeyError):
            ConversationGraph(service).turns(first)

    def test_selection_isolation_and_typed_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FakeService()
            client = TestClient(create_app(service, Path(directory)))
            first = client.post("/api/sessions").json()["id"]
            second = client.post("/api/sessions").json()["id"]
            client.post(f"/api/sessions/{first}/chat", json={"message": "Hello"})
            request = {
                "message": "Explain",
                "artifact_id": "artifact",
                "element_id": "n1",
            }
            self.assertEqual(
                client.post(f"/api/sessions/{second}/chat", json=request).status_code,
                422,
            )
            self.assertEqual(
                client.post(f"/api/sessions/{first}/chat", json=request).status_code,
                200,
            )
            self.assertEqual(service.selection["source_ids"], ["source1"])
            service.fail = True
            failure = client.post(
                f"/api/sessions/{first}/chat", json={"message": "Another"}
            )
            self.assertEqual(failure.status_code, 429)
            self.assertEqual(failure.json()["code"], "budget_exhausted")

    def test_context_window(self):
        turns = [
            {"question": str(i), "answer": {"blocks": [{"text": "An answer"}]}}
            for i in range(20)
        ]
        history = history_window(turns)
        self.assertEqual(len(history), 12)
        self.assertEqual(history[-2]["text"], "19")


if __name__ == "__main__":
    unittest.main()
