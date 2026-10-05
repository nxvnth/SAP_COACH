"""Grounded response and semantic diagram contracts, independent of renderer."""

# READER GUIDE
# Data contracts and the final boundary before model text reaches the UI.
# Pydantic checks field names, types and size limits. Additional checks verify
# that cited IDs are in this request's evidence and diagram endpoints exist.
# A canonical source ID identifies an ingested object; a node/edge ID identifies
# an element within a generated diagram. They are not interchangeable.
# normalize_answer can salvage cited text when optional parts are unusable:
# uncited paragraphs are omitted with a notice; invalid diagrams are omitted.
# It does not invent a citation, prove factual entailment, or silently accept an
# unknown source ID. Read validate_answer first, then normalize_answer.

import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# All response models reject unexpected fields so provider output cannot silently change the app contract.
class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# A paragraph stores source IDs separately from its learner-facing text.
class Block(Strict):
    text: str = Field(min_length=1, max_length=3000)
    source_ids: list[str] = Field(max_length=12)


# Diagram elements carry factual evidence or explicitly mark themselves as explanatory groupings.
class Node(Strict):
    id: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=70)
    explanation: str = Field(min_length=1, max_length=700)
    source_ids: list[str] = Field(max_length=8)
    explanatory: bool


# An edge has the same label/explanation/source fields as a node, plus its two endpoint IDs.
class Edge(Node):
    source: str
    target: str


class Diagram(Strict):
    title: str = Field(min_length=1, max_length=120)
    nodes: list[Node] = Field(min_length=1, max_length=8)
    edges: list[Edge] = Field(max_length=12)


class Answer(Strict):
    status: Literal["grounded", "partial", "insufficient"]
    blocks: list[Block] = Field(min_length=1, max_length=8)
    diagram: Diagram | None
    followups: list[str] = Field(max_length=3)
    clarification: str | None = Field(default=None, max_length=500)


# Check shape and source-ID membership. This cannot prove that a cited passage supports every claim.
def validate_answer(raw, evidence):
    answer = Answer.model_validate(raw)
    # Only sources actually retrieved for this answer are valid citations.
    allowed = set(evidence)
    if answer.status == "insufficient" and answer.diagram:
        raise ValueError("Insufficient answers cannot assert a diagram")
    for block in answer.blocks:
        if not set(block.source_ids) <= allowed:
            raise ValueError("Unknown citation")
        if answer.status in {"grounded", "partial"} and not block.source_ids:
            raise ValueError("Grounded paragraph needs citations")
    d = answer.diagram
    if d:
        ids = [n.id for n in d.nodes]
        edge_ids = [e.id for e in d.edges]
        if len(set(ids + edge_ids)) != len(ids + edge_ids):
            raise ValueError("Duplicate diagram IDs")
        for e in d.edges:
            if e.source not in ids or e.target not in ids or e.source == e.target:
                raise ValueError("Dangling edge")
        for item in [*d.nodes, *d.edges]:
            if not set(item.source_ids) <= allowed:
                raise ValueError("Unknown diagram source")
            if not item.explanatory and not item.source_ids:
                raise ValueError("Uncited factual element")
        # Artifact IDs persist with a saved turn; source IDs stay separate and canonical.
    return answer.model_dump()


def normalize_answer(raw, evidence):
    """Validate text first. A broken optional diagram must not discard a valid answer."""
    # Temporarily exclude the optional diagram from the first validation pass.
    # A malformed arrow or missing node must not prevent checking useful prose.
    text_only = dict(raw, diagram=None)
    # A model may put an evidence-gap explanation in an uncited paragraph.
    # We cannot reliably distinguish that from an uncited factual claim by wording.
    # Preserve only cited paragraphs, disclose the omission, and never invent citations.
    candidate = Answer.model_validate(text_only)
    # Unknown IDs remain fatal even if another paragraph could be shown.
    # An empty citation list is different: that paragraph can be omitted, but
    # only if at least one cited paragraph survives in a grounded/partial answer.
    for block in candidate.blocks:
        if not set(block.source_ids) <= set(evidence):
            raise ValueError("Unknown citation")
    omitted_uncited = False
    if candidate.status in {"grounded", "partial"}:
        cited = [block for block in candidate.blocks if block.source_ids]
        if not cited:
            raise ValueError("Grounded paragraph needs citations")
        if len(cited) != len(candidate.blocks):
            text_only = candidate.model_dump()
            text_only["blocks"] = [block.model_dump() for block in cited]
            text_only["status"] = "partial"
            omitted_uncited = True
    result = validate_answer(text_only, evidence)
    result["notices"] = []
    if omitted_uncited:
        result["notices"].append(
            "Some uncited text was omitted. This answer covers only the cited material."
        )
    # Canonical IDs belong in source_ids, never in learner-facing paragraphs.
    for block in result["blocks"]:
        block["text"] = re.sub(r"\ue200cite\ue202[^\ue201]*\ue201", "", block["text"])
        block["text"] = re.sub(
            r"\[[^\]\n]*[\w-]+:(?:paragraph|figure|heading|procedure|table|table_row|code|callout):[^\]\n]*\]",
            "",
            block["text"],
        )
        block["text"] = re.sub(
            r"\b[\w-]+:(?:paragraph|figure|heading|procedure|table|table_row|code|callout):[\w-]+",
            "",
            block["text"],
        )
        block["text"] = re.sub(r"[ \t]{2,}", " ", block["text"]).strip()
        if not block["text"]:
            raise ValueError("Empty answer after citation cleanup")
        block["source_ids"] = list(dict.fromkeys(block["source_ids"]))
    suggestions = []
    for question in result["followups"]:
        # Defense against assistant-to-learner questions becoming clickable learner text.
        if re.match(
            r"(?i)^(?:do|would) you (?:want|like)|^(?:can|could|would) you (?:provide|share|tell|confirm|specify)|^do you have",
            question.strip(),
        ):
            if not result["clarification"]:
                result["clarification"] = question
        else:
            suggestions.append(question)
    result["followups"] = suggestions
    # A valid text answer can stand alone; diagram errors should not discard it.
    if not raw.get("diagram"):
        return result
    if result["status"] == "insufficient":
        result["notices"].append(
            "The diagram was omitted because the available evidence is incomplete."
        )
        return result
    try:
        checked = validate_answer(dict(text_only, diagram=raw["diagram"]), evidence)
        result["diagram"] = checked["diagram"]
    except ValueError:
        result["notices"].append(
            "The answer is available, but the diagram did not pass source and structure checks."
        )
    return result


# The intent result tells the graph whether to search, use a selection, or ask for clarification.
class QueryIntent(Strict):
    relationship: Literal["standalone", "followup", "selection", "ambiguous"]
    standalone_question: str = Field(max_length=1600)
    use_selection: bool
    clarification: str = Field(max_length=400)


def validate_intent(raw, message, selection):
    """Reject inconsistent plans and loss of explicit technical constraints."""
    intent = QueryIntent.model_validate(raw).model_dump()
    if intent["relationship"] == "standalone":
        intent["standalone_question"] = message
        intent["use_selection"] = False
    if intent["use_selection"] and not selection:
        raise ValueError("Selected context requested without a selection")
    if intent["relationship"] == "ambiguous":
        if not intent["clarification"].strip():
            raise ValueError("Ambiguous intent needs a clarification")
        intent["standalone_question"] = ""
        intent["use_selection"] = False
    elif not intent["standalone_question"].strip():
        raise ValueError("Resolved intent needs a query")
    if intent["relationship"] != "ambiguous":
        # Protect explicit underscored identifiers, command flags and versions from disappearing in a rewrite.
        identifiers = re.findall(
            r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b|--[A-Za-z0-9_-]+|\b\d+\.\d+(?:\.\d+)*\b",
            message,
        )
        if any(
            identifier.lower() not in intent["standalone_question"].lower()
            for identifier in identifiers
        ):
            raise ValueError("Query rewrite lost an explicit identifier or version")
    return intent
