"""Local embeddings, evidence units and token-bounded passage windows."""

# READER GUIDE
# Shared embedding and evidence primitives.
# units() renders objects as source-bearing text: procedures refer to child
# objects, and table rows carry their column headings so isolated values make sense.
# ancestors() walks document sections to supply location/context breadcrumbs.
# load_model() uses bundled local BGE weights; rank() embeds only the query and
# compares it with precomputed passage vectors. Documents are not re-embedded
# for each chat turn. evidence_covered() merges token spans to distinguish full
# coverage from a matching fragment; similarity alone does not establish coverage.

from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path

# Force local model loading; normal chat retrieval must not download weights from the model hub.
os.environ.update(
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    HF_HUB_DISABLE_TELEMETRY="1",
    TOKENIZERS_PARALLELISM="false",
)
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from ..settings import APP_DIR

CONFIG_PATH = Path(__file__).with_name("embedding_model.json")


def read(p):
    return json.loads(p.read_text())


def save(p, v):
    p.write_text(json.dumps(v, indent=2, ensure_ascii=False) + "\n")


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clean(s):
    return " ".join(s.split())


def units(o, by):
    """Produce evidence units, independently of test questions."""
    if o["type"] == "procedure":
        ids = (
            o.get("prerequisite_ids", [])
            + [i for s in o["steps"] for i in s["object_ids"]]
            + o.get("result_ids", [])
        )
        return [u for i in dict.fromkeys(ids) for u in units(by[i], by)]
    if o["type"] == "table":
        lines = ["Columns: " + " | ".join(map(clean, o["headers"]))]
        lines += [
            " | ".join(
                f"{clean(h)}: {clean(c)}" for h, c in zip(o["headers"], row["cells"])
            )
            for row in o["rows"]
        ]
        return [(o["id"], "\n".join(lines))]
    if o["type"] == "table_row":
        text = " | ".join(
            f"{clean(h)}: {clean(c)}" for h, c in zip(o["headers"], o["cells"])
        )
        if o.get("exact_key"):
            text += "\nParameter identifier: " + o["exact_key"]
        return [(o["id"], text)]
    return [(o["id"], o["text"])]


# Follow document parents to build a section breadcrumb; these are document links, not domain graph edges.
def ancestors(o, by):
    nodes = []
    pid = o["parent_id"]
    while pid:
        p = by[pid]
        if p["type"] == "section":
            nodes.append(p.get("title", p["text"]))
        pid = p["parent_id"]
    return list(reversed(nodes))


# Use the packaged embedding revision on CPU, with the same sequence limit used to build the index.
def load_model():
    config = read(CONFIG_PATH)
    torch.set_num_threads(4)
    model = SentenceTransformer(
        str(APP_DIR / config["local_path"]),
        device="cpu",
        local_files_only=True,
        trust_remote_code=False,
    )
    model.max_seq_length = 512
    return config, model


def rank(query, model, cfg, rows, vectors):
    text = cfg["query_prefix"] + query
    if len(model.tokenizer.encode(text)) > 512:
        raise ValueError("Query exceeds 512-token limit; shorten it.")
    t = time.perf_counter()
    q = model.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]
    # Both index and query vectors are normalized, so their dot product is cosine similarity.
    scores = vectors @ q
    order = np.argsort(-scores, kind="stable")
    # Several windows may belong to one object; retain its highest-scoring window once.
    seen = set()
    hits = []
    for i in order:
        r = rows[int(i)]
        if r["canonical_id"] in seen:
            continue
        seen.add(r["canonical_id"])
        hits.append(dict(rank=len(hits) + 1, score=float(scores[i]), **r))
    return hits, (time.perf_counter() - t) * 1000


# An evidence ID is complete only if its retrieved token spans cover the original unit without gaps.
def evidence_covered(hits):
    spans = {}
    for h in hits:
        for s in h["evidence"]:
            spans.setdefault(s["id"], []).append(s)
    complete = set()
    for oid, ss in spans.items():
        end = 0
        for s in sorted(ss, key=lambda s: s["start"]):
            if s["start"] > end:
                break
            end = max(end, s["end"])
        if end >= max(s["total"] for s in ss):
            complete.add(oid)
    return complete
