"""Build overlapping embedding windows while retaining canonical evidence spans."""

# READER GUIDE
# Turn source objects into embedding inputs without losing citation links.
# Objects are logical content units; windows are token-limited slices that the
# embedding model can accept. Several windows may point to the same canonical ID.
# Each window repeats a section/procedure prefix, then contains a slice of body
# tokens. The prefix uses at most 160 tokens; the entire input stays within 512;
# neighboring body slices overlap by 48 tokens to soften boundary losses.
# Evidence spans record start/end offsets relative to original source units,
# excluding prefix tokens. Retrieval uses these offsets to recover source text
# and recognize when only part of a procedure or paragraph was actually retrieved.

from ..retrieval.vector import ancestors, units


# Convert eligible source objects into model-sized windows while preserving links to their original text.
def passages(objects, tokenizer):
    by = {o["id"]: o for o in objects}
    result = []
    allowed = {"paragraph", "code", "callout", "table_row", "figure", "procedure"}
    for o in objects:
        path = ancestors(o, by)
        if (
            not o.get("indexable")
            or o["type"] not in allowed
            or any("Learning Assessment" in x for x in path)
        ):
            continue
        if o.get("role") == "related_information" or not any(
            c.isalnum() for c in o["text"]
        ):
            continue
        # Headings/whole tables are retained in store, not separately ranked in R0.
        prefix = " > ".join(path) + "\n"
        if o["type"] == "procedure":
            prefix += o["text"] + "\n"
        # Reserve up to 160 tokens for the section/procedure breadcrumb that gives each window context.
        pt = tokenizer.encode(prefix, add_special_tokens=False)[:160]
        body = []
        spans = []
        for oid, text in units(o, by):
            ts = tokenizer.encode(text + "\n", add_special_tokens=False)
            if ts:
                spans.append(dict(id=oid, start=len(body), end=len(body) + len(ts)))
                body += ts
        if not body:
            continue
        # The 512-token model limit includes special tokens and the prefix; neighboring windows overlap by 48 tokens.
        capacity = 512 - tokenizer.num_special_tokens_to_add(pair=False) - len(pt)
        for start in range(0, len(body), capacity - 48):
            end = min(start + capacity, len(body))
            ids = pt + body[start:end]
            text = tokenizer.decode(
                ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            # Decoding and re-tokenizing must not silently overflow the model.
            length = len(tokenizer.encode(text, add_special_tokens=True))
            if length > 512:
                raise ValueError(f'Window overflow: {o["id"]} {length}')
            # Store offsets relative to each original unit so retrieval can distinguish partial from complete evidence.
            # Example: a 100-token source unit intersecting this window at tokens
            # 40..80 records start=40, end=80, total=100. Finding that window alone
            # does not mean the whole unit was retrieved.
            evidence = [
                dict(
                    id=s["id"],
                    start=max(start, s["start"]) - s["start"],
                    end=min(end, s["end"]) - s["start"],
                    total=s["end"] - s["start"],
                )
                for s in spans
                if s["start"] < end and s["end"] > start
            ]
            result.append(
                dict(
                    window_id=o["id"] + f":w{start}",
                    canonical_id=o["id"],
                    type=o["type"],
                    text=text,
                    token_count=length,
                    source=o["source"],
                    evidence=evidence,
                    visual_content_available=False if o["type"] == "figure" else None,
                )
            )
            if end == len(body):
                break
    return result
