"""Normalize repeated procedural numbering without inventing steps."""

from . import extractor as x


# original is the set of IDs to leave untouched; new candidate datasets pass an empty set.
def normalize_procedures(ex, original):
    by = {o["id"]: o for o in ex.objects}
    replacement = []
    remove = set()
    for proc in list(ex.objects):
        if proc["type"] != "procedure" or proc["id"] in original:
            continue
        groups = []
        current = []
        # Supplementary links are not part of the last procedural action.
        ended = False
        for step in proc["steps"]:
            if ended:
                break
            kept = []
            for oid in step["object_ids"]:
                if x.tidy(by[oid]["text"]) == "Further Information":
                    ended = True
                    break
                kept.append(oid)
            step = dict(step, object_ids=kept)
            if not kept:
                continue
            first = by[step["object_ids"][0]]
            # A repeated/lower number may start a new procedure or be an indented substep in the HANA profile.
            if current and step["number"] <= current[-1]["number"]:
                prev = by[current[-1]["object_ids"][0]]
                if (
                    first["source"][0]["document_id"] == "hana-sps08"
                    and first["source"][0]["bbox"][0] > prev["source"][0]["bbox"][0] + 5
                ):
                    current[-1]["object_ids"] += step["object_ids"]
                    continue
                # If the indentation rule did not identify a substep, begin a separate numbered sequence.
                groups.append(current)
                current = []
            current.append(step.copy())
        if current:
            groups.append(current)
        if len(groups) == 1:
            proc["steps"] = groups[0]
        else:
            remove.add(proc["id"])
            for index, steps in enumerate(groups):
                first = by[steps[0]["object_ids"][0]]
                item = dict(
                    proc,
                    id=x.stable(
                        first["source"][0]["document_id"],
                        "procedure",
                        first["source"][0]["pdf_page"],
                        first["source"][0]["bbox"],
                        f"sequence-{index}",
                    ),
                    steps=steps,
                    text=proc["text"] + f" — numbered sequence {index+1}",
                    extraction_status="split_repeated_numbering_requires_title_review",
                )
                item["source"] = [
                    loc
                    for step in steps
                    for oid in step["object_ids"]
                    for loc in by[oid]["source"]
                ]
                replacement.append(item)
    # Apply replacements after iteration so changing the inventory does not disturb the scan.
    ex.objects = [o for o in ex.objects if o["id"] not in remove] + replacement
    ex.issues = [
        i
        for i in ex.issues
        if not (i["code"] == "procedure_numbering" and i["object_id"] not in original)
    ]
    for o in ex.objects:
        if o["type"] == "procedure" and [s["number"] for s in o["steps"]] != list(
            range(1, len(o["steps"]) + 1)
        ):
            ex.issue(
                "procedure_numbering", o, "Unresolved numbering; source review needed"
            )
