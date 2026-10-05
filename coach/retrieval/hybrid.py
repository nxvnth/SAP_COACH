"""R1: parallel lexical/vector/structural retrieval and bounded original-source context.
No question labels are visible to the search or context-building methods.
"""

from __future__ import annotations
import collections, concurrent.futures, math, re, time
from pathlib import Path
import numpy as np
from . import vector
from ..settings import DATASET_DIR
from .index_store import validate_index

# Shared search defaults. The app passes its top-ten cutoff explicitly when assembling context.
POLICY = dict(
    version="r1-v1",
    channel_k=20,
    rrf_k=60,
    bm25_k1=1.2,
    bm25_b=0.75,
    top_k=5,
    context_budget=4096,
    enrichment="atomic procedure expansion; original source blocks; deduplicate evidence IDs; no domain graph",
    structured="exact parameter keys/canonical IDs; procedure title lexical overlap >= 0.4 with at least two shared terms",
    aliases={"gui": "graphical user interface", "cli": "command line interface"},
    reranker=None,
)
STOP = set(
    "a an the of for to in on at and or is are be by with from what which how do does me through this its i it my we can as before after".split()
)


def tokens(text):
    # Keep identifiers intact; also expose their lexical components.
    out = []
    for t in re.findall(r"[a-z0-9]+(?:[_.-][a-z0-9]+)*", text.lower()):
        if t not in STOP:
            out.append(t)
        if re.search(r"[_.-]", t):
            out.extend(p for p in re.split("[_.-]", t) if p and p not in STOP)
    return out


def title_tokens(text):
    for alias, full in POLICY["aliases"].items():
        text = re.sub(r"\b" + alias + r"\b", full, text, flags=re.I)
    return {
        t for t in tokens(text) if not t.isdigit() and not re.fullmatch(r"[\d.]+", t)
    }


# Lexical retrieval scores exact words/identifiers, complementing the embedding model’s semantic matches.
class BM25:
    def __init__(self, docs):
        self.docs = [collections.Counter(tokens(d)) for d in docs]
        self.length = np.array([sum(d.values()) for d in self.docs])
        self.avg = float(self.length.mean()) or 1
        self.df = collections.Counter(t for d in self.docs for t in d)

    def score(self, query):
        scores = np.zeros(len(self.docs))
        n = len(self.docs)
        for t in set(tokens(query)):
            df = self.df.get(t, 0)
            if not df:
                continue
            # Rare terms receive more weight. tf measures occurrences; document length adjusts the contribution.
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            tf = np.array([d.get(t, 0) for d in self.docs])
            # k controls how quickly repeated occurrences stop adding value; b controls length normalization.
            k = POLICY["bm25_k1"]
            b = POLICY["bm25_b"]
            scores += (
                idf * tf * (k + 1) / (tf + k * (1 - b + b * self.length / self.avg))
            )
        return scores


# Reciprocal-rank fusion combines channel positions, since BM25 and vector raw scores use different scales.
def fuse(channels):
    merged = {}
    for name, hits in channels.items():
        seen = set()
        for rank, hit in enumerate(hits, 1):
            oid = hit["canonical_id"]
            if oid in seen:
                continue
            seen.add(oid)
            m = merged.setdefault(
                oid, dict(canonical_id=oid, score=0.0, channels={}, representative=hit)
            )
            # Each channel votes by rank; rrf_k smooths the advantage of being first.
            contribution = 1 / (POLICY["rrf_k"] + rank)
            m["score"] += contribution
            m["channels"][name] = dict(
                rank=rank,
                raw_score=hit["score"],
                rrf_contribution=contribution,
                reason=hit.get("reason"),
            )
            # Vector winning window is retained when available, for a clean no-enrichment comparison.
            if name == "vector":
                m["representative"] = hit
    return [
        dict(rank=i + 1, **v)
        for i, v in enumerate(
            sorted(merged.values(), key=lambda m: (-m["score"], m["canonical_id"]))
        )
    ]


# Own the loaded index and three search channels; no answer generation or domain knowledge graph runs here.
class Hybrid:
    def __init__(self, data_dir=None):
        data_dir = Path(data_dir) if data_dir is not None else DATASET_DIR
        self.cfg, self.model = vector.load_model()
        self.tok = self.model.tokenizer
        validate_index(data_dir, self.cfg)
        self.objects = vector.read(data_dir / "inventory.json")
        self.by = {o["id"]: o for o in self.objects}
        self.rows = vector.read(data_dir / "passages.json")
        self.vectors = np.load(data_dir / "vectors.npy", allow_pickle=False)
        # Recover source text using token offsets rather than treating decoded embedding windows as exact quotations.
        self.original = {}
        self.byanchor = collections.defaultdict(list)
        for row in self.rows:
            oid = row["canonical_id"]
            self.byanchor[oid].append(row)
            units = dict(vector.units(self.by[oid], self.by))
            parts = []
            for span in row["evidence"]:
                text = units[span["id"]] + "\n"
                offsets = self.tok(
                    text,
                    add_special_tokens=False,
                    return_offsets_mapping=True,
                    verbose=False,
                )["offset_mapping"]
                if span["end"] > len(offsets):
                    raise ValueError("Evidence token offsets drifted")
                a = offsets[span["start"]][0]
                b = offsets[span["end"] - 1][1]
                parts.append(
                    dict(
                        id=span["id"],
                        text=text[a:b],
                        source=self.by[span["id"]]["source"],
                    )
                )
            self.original[row["window_id"]] = parts
        self.lexical_texts = [
            " > ".join(vector.ancestors(self.by[row["canonical_id"]], self.by))
            + "\n"
            + "\n".join(p["text"] for p in self.original[row["window_id"]])
            for row in self.rows
        ]
        self.bm = BM25(self.lexical_texts)
        self.procedures = [
            o
            for o in self.objects
            if o["type"] == "procedure" and o["id"] in self.byanchor
        ]
        self.keys = collections.defaultdict(list)
        for oid in self.byanchor:
            if self.by[oid].get("exact_key"):
                self.keys[self.by[oid]["exact_key"].lower()].append(oid)
        # Map individual source objects to containing procedures so a step can lead to the whole procedure.
        self.owners = collections.defaultdict(list)
        for proc in self.procedures:
            for oid, _ in vector.units(proc, self.by):
                self.owners[oid].append(proc["id"])
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    def close(self):
        self.pool.shutdown()

    # Rank passage windows by keyword score, then keep at most one result for each canonical object.
    def lexical(self, query):
        scores = self.bm.score(query)
        seen = set()
        hits = []
        for i in np.argsort(-scores, kind="stable"):
            if scores[i] <= 0:
                break
            row = self.rows[int(i)]
            oid = row["canonical_id"]
            if oid in seen:
                continue
            seen.add(oid)
            hits.append(dict(**row, score=float(scores[i])))
            if len(hits) == POLICY["channel_k"]:
                break
        return hits

    # Add deterministic matches for exact identifiers and sufficiently overlapping procedure titles.
    def structured(self, query):
        hits = {}
        qt = set(tokens(query))
        terms = title_tokens(query)

        def add(oid, score, reason):
            if oid not in hits or score > hits[oid]["score"]:
                hits[oid] = dict(**self.byanchor[oid][0], score=score, reason=reason)

        for oid in self.byanchor:
            if oid in query:
                add(oid, 3.0, "literal canonical ID")
        # Compare intact query identifiers, not their split components.
        literals = set(re.findall(r"[a-z0-9]+(?:[_.-][a-z0-9]+)*", query.lower()))
        for key, oids in self.keys.items():
            if key in literals:
                for oid in oids:
                    add(oid, 2.0, "exact parameter key: " + key)
        for proc in self.procedures:
            pt = title_tokens(proc["text"])
            common = terms & pt
            overlap = len(common) / max(1, len(terms | pt))
            if len(common) >= 2 and overlap >= 0.4:
                add(
                    proc["id"],
                    overlap,
                    "procedure title overlap; GUI/CLI alias normalization",
                )
        return sorted(hits.values(), key=lambda h: (-h["score"], h["canonical_id"]))[
            : POLICY["channel_k"]
        ]

    # Run independent vector, keyword and structural searches concurrently, then combine their rankings.
    def search(self, query):
        t = time.perf_counter()
        vf = self.pool.submit(
            vector.rank, query, self.model, self.cfg, self.rows, self.vectors
        )
        bf = self.pool.submit(self.lexical, query)
        sf = self.pool.submit(self.structured, query)
        vector_hits, vector_ms = vf.result()
        channels = dict(
            vector=vector_hits[: POLICY["channel_k"]],
            bm25=bf.result(),
            structured=sf.result(),
        )
        fused = fuse(channels)
        return fused, vector_hits, channels, (time.perf_counter() - t) * 1000

    def context_units(self, target):
        return vector.units(self.by[target], self.by), None

    # Turn ranked anchors into cited source excerpts, deduplicate them, and enforce the token budget.
    def context(self, hits, query, enrich, top_k=None):
        cutoff = POLICY["top_k"] if top_k is None else top_k
        start = time.perf_counter()
        items = []
        seen = set()
        complete = set()
        used = 0
        skipped = []
        partial = []
        plans = []
        procedure_request = bool(
            re.search(
                r"\b(steps?|sequence|procedure|prerequisites?|order)\b|walk me|how do",
                query,
                re.I,
            )
        )
        for h in hits[:cutoff]:
            oid = h["canonical_id"]
            o = self.by[oid]
            target = oid
            reason = "selected original object"
            if enrich and o["type"] == "procedure":
                reason = "complete ordered procedure"
            elif enrich and procedure_request and self.owners.get(oid):
                # At most one direct containing procedure; never traverse unrelated neighbors.
                target = self.owners[oid][0]
                reason = "direct containing procedure for procedural question"
            if enrich:
                units, group_reason = self.context_units(target)
                if group_reason:
                    reason = group_reason
                content = [
                    dict(id=i, text=text, source=self.by[i]["source"])
                    for i, text in units
                ]
                coverage = {p["id"] for p in content}
            else:
                rep = h.get("representative", h)
                content = self.original[rep["window_id"]]
                coverage = vector.evidence_covered([rep])
                partial.append(rep)
                reason = "winning source window; no expansion"
            fresh = [p for p in content if p["id"] not in seen] if enrich else content
            # Include citation labels in the measured context budget.
            rendered = "\n\n".join(f"[{p['id']}]\n{p['text']}" for p in fresh)
            count = (
                len(self.tok.encode(rendered, add_special_tokens=False, verbose=False))
                if fresh
                else 0
            )
            # Expansion is atomic: skip an oversized unit rather than silently returning a cut-off procedure.
            if used + count > POLICY["context_budget"]:
                skipped.append(
                    dict(
                        anchor_id=oid,
                        expanded_id=target,
                        reason="atomic expansion exceeds remaining token budget",
                        tokens=count,
                    )
                )
                continue
            used += count
            complete.update(coverage)
            for p in fresh:
                items.append(dict(**p, from_anchor=oid, expansion_reason=reason))
                seen.add(p["id"])
            plans.append(
                dict(
                    anchor_id=oid,
                    expanded_id=target,
                    reason=reason,
                    source_ids=[p["id"] for p in content],
                    included=True,
                )
            )
        if not enrich:
            complete = vector.evidence_covered(
                [
                    h.get("representative", h)
                    for h in hits[:cutoff]
                    if h["canonical_id"] not in {s["anchor_id"] for s in skipped}
                ]
            )
        return dict(
            items=items,
            complete_evidence_ids=sorted(complete),
            tokens=used,
            skipped=skipped,
            expansion_plans=plans,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
