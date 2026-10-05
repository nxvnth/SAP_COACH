"""Local, deterministic PDF extraction profiles. No LLM, OCR, or network calls.
Profiles are provisional and intentionally scoped to the supplied PDF editions.
"""

from __future__ import annotations
import argparse, collections, hashlib, html, json, re
from pathlib import Path
import pymupdf as pdf

from ..settings import DOCUMENTS_DIR


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def tidy(s):
    return re.sub(r"\s+", " ", s).strip()


# Normalize PDF rectangle coordinates to stable rounded values for source locations and IDs.
def box(r):
    return [round(float(v), 2) for v in r]


def union(items):
    r = pdf.Rect(items[0])
    for b in items[1:]:
        r |= pdf.Rect(b)
    return box(r)


# Keep both PDF page and printed-page labels; this mapping is specific to the supported editions.
def loc(key, page, bbox):
    return dict(
        document_id=key,
        pdf_page=page,
        printed_page=str(page - 8 if key.startswith("adm") else page),
        bbox=box(bbox),
    )


def stable(key, typ, page, bbox, extra=""):
    # Stable within a fixed PDF edition and extraction profile; no text/model summary in the key.
    token = f"{key}|{typ}|{page}|{box(bbox)}|{extra}"
    return key + ":" + typ + ":" + hashlib.sha256(token.encode()).hexdigest()[:12]


# Retain font and rectangle information alongside text, because layout helps identify headings and tables.
def lines_on(page):
    result = []
    for bi, b in enumerate(page.get_text("dict")["blocks"]):
        if b["type"] != 0:
            continue
        for li, l in enumerate(b["lines"]):
            spans = l["spans"]
            result.append(
                dict(
                    text="".join(s["text"] for s in spans),
                    bbox=box(l["bbox"]),
                    block=bi,
                    line=li,
                    spans=[
                        dict(
                            text=s["text"],
                            font=s["font"],
                            size=round(s["size"], 2),
                            bbox=box(s["bbox"]),
                        )
                        for s in spans
                    ],
                )
            )
    return result


# Collect text spans inside a cell rectangle rather than flattening neighboring columns together.
def cell(lines, x0, y0, x1, y1):
    selected = []
    for l in lines:
        spans = [
            s
            for s in l["spans"]
            if x0 - 0.3 <= s["bbox"][0] < x1 - 0.3
            and y0 <= (s["bbox"][1] + s["bbox"][3]) / 2 < y1
        ]
        if spans:
            selected.append(
                (l["bbox"][1], l["bbox"][0], "".join(s["text"] for s in spans))
            )
    return "\n".join(t[2] for t in sorted(selected))


def geometry_tables(page, lines):
    """Infer columns from segmented horizontal rules, not whole-page text clustering."""
    ys = collections.defaultdict(list)
    for d in page.get_drawings():
        r = d["rect"]
        if (
            d["type"] == "s"
            and r.height < 0.8
            and r.width > 20
            and r.y0 < page.rect.height - 55
        ):
            ys[round(r.y0, 1)].append((r.x0, r.x1))
    rules = []
    for y, segs in sorted(ys.items()):
        xs = []
        for x in sorted(v for s in segs for v in s):
            if not xs or x - xs[-1] > 0.8:
                xs.append(x)
        if len(xs) < 3:
            continue
        # Multi-column medium-font labels directly above a rule identify a table header.
        heads = [
            s
            for l in lines
            for s in l["spans"]
            if "Medium" in s["font"]
            and s["size"] <= 9
            and y - 36 < s["bbox"][1] < y
            and s["bbox"][3] <= y + 1
        ]
        cols = {
            next(
                (
                    i
                    for i in range(len(xs) - 1)
                    if xs[i] - 0.5 <= s["bbox"][0] < xs[i + 1] - 0.5
                ),
                -1,
            )
            for s in heads
        }
        is_header = (
            len(cols - {-1}) >= 2
            and y - max((s["bbox"][3] for s in heads), default=0) < 10
        )
        rules.append(
            dict(
                y=y,
                xs=xs,
                header=is_header,
                head_y=min((s["bbox"][1] for s in heads), default=y - 16),
            )
        )
    groups = []
    for r in rules:
        same = (
            bool(groups)
            and len(groups[-1][-1]["xs"]) == len(r["xs"])
            and all(abs(a - b) < 1 for a, b in zip(groups[-1][-1]["xs"], r["xs"]))
        )
        if not same or r["header"]:
            groups.append([r])
        else:
            groups[-1].append(r)
    out = []
    for g in groups:
        if len(g) < 2:
            continue
        xs = g[0]["xs"]
        y0 = g[0]["head_y"] - 1 if g[0]["header"] else 100
        headers = (
            [cell(lines, xs[i], y0, xs[i + 1], g[0]["y"]) for i in range(len(xs) - 1)]
            if g[0]["header"]
            else []
        )
        bounds = [g[0]["y"]] + [r["y"] for r in g[1:]]
        if not g[0]["header"]:
            bounds = [y0] + bounds
        rows = []
        for a, b in zip(bounds, bounds[1:]):
            vals = [cell(lines, xs[i], a, xs[i + 1], b) for i in range(len(xs) - 1)]
            if any(v.strip() for v in vals):
                rows.append(dict(cells=vals, bbox=box([xs[0], a, xs[-1], b])))
        out.append(
            dict(
                bbox=box([xs[0], y0, xs[-1], g[-1]["y"]]),
                headers=headers,
                rows=rows,
                column_boundaries=[round(v, 2) for v in xs],
                method="segmented_horizontal_rules",
                needs_review=not bool(headers),
            )
        )
    return out


# Accumulate canonical content, raw lines, source provenance and review issues for configured PDF ranges.
class Extractor:
    def __init__(self, out, documents_dir=DOCUMENTS_DIR):
        self.documents_dir = Path(documents_dir)
        self.out = out
        self.objects = []
        self.raw = []
        self.manifest = []
        self.issues = []
        self.tables = []
        (out / "assets").mkdir(parents=True, exist_ok=True)

    # Give every object a stable source-based ID, parent link and default search eligibility.
    def add(self, key, typ, text, page, bbox, parent=None, **kw):
        o = dict(
            id=stable(key, typ, page, bbox, kw.pop("id_extra", "")),
            type=typ,
            text=text,
            parent_id=parent,
            source=[loc(key, page, bbox)],
            indexable=typ
            not in {
                "section",
                "heading",
                "objective",
                "summary",
                "assessment",
                "assessment_answer",
            },
            **kw,
        )
        if "indexable_override" in o:
            o["indexable"] = o.pop("indexable_override")
        self.objects.append(o)
        return o

    def issue(self, code, obj, detail):
        self.issues.append(dict(code=code, object_id=obj["id"], detail=detail))

    # Process one document range: outline → page objects → procedures/assessments → contextual links.
    def process(self, cfg):
        key = cfg["key"]
        path = self.documents_dir / cfg["file"]
        d = pdf.open(path)
        self.manifest.append(
            dict(
                **cfg,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                total_pages=len(d),
                full_outline=d.get_toc(),
                printed_page_mapping=(
                    "PDF page - 8 (verified selected slice)"
                    if cfg["profile"] == "tadm"
                    else "PDF page (verified selected slice)"
                ),
            )
        )
        page_lines = {
            n: lines_on(d[n - 1]) for n in range(cfg["start"], cfg["end"] + 1)
        }
        nodes = []
        stack = []
        # Use PDF bookmarks to build the document hierarchy, then locate headings within each page.
        for depth, title, n in d.get_toc():
            if not cfg["start"] <= n <= cfg["end"]:
                continue
            if cfg["profile"] == "tadm" and depth > 2:
                continue  # same-title lesson bookmarks are aliases here
            ls = page_lines[n]
            if cfg["profile"] == "hana":
                number = title.split()[0]
                match = [
                    l
                    for l in ls
                    if max(s["size"] for s in l["spans"]) >= 14
                    and re.match(r"^" + re.escape(number) + r"(?:\s|$)", l["text"])
                ]
            else:
                marker = (
                    re.match(r"Unit \d+", title).group().upper()
                    if depth == 1
                    else re.match(r"Lesson \d+", title).group()
                )
                match = [l for l in ls if tidy(l["text"]).lower() == marker.lower()]
            y = match[0]["bbox"][1] if match else 0
            while stack and stack[-1]["depth"] >= depth:
                stack.pop()
            node = self.add(
                key,
                "section",
                title,
                n,
                [0, y, d[n - 1].rect.width, y + 1],
                stack[-1]["id"] if stack else None,
                title=title,
                depth=depth,
            )
            if not match:
                self.issue(
                    "heading_unresolved",
                    node,
                    "Bookmark heading could not be matched to text geometry.",
                )
            stack.append(node)
            nodes.append((n, y, node))
        if cfg["profile"] == "tadm":
            unit = nodes[0][2]
            for n, ls in page_lines.items():
                for l in ls:
                    if tidy(l["text"]) in {
                        "Learning Assessment",
                        "Learning Assessment - Answers",
                    }:
                        node = self.add(
                            key,
                            "section",
                            tidy(l["text"]),
                            n,
                            l["bbox"],
                            unit["id"],
                            title=tidy(l["text"]),
                            depth=2,
                        )
                        nodes.append((n, l["bbox"][1], node))
        nodes.sort(key=lambda t: (t[0], t[1]))

        # Assign an object to the latest section heading preceding its page and vertical position.
        def parent(n, y):
            eligible = [v for p, z, v in nodes if (p, z) <= (n, y + 0.5)]
            return (eligible[-1] if eligible else nodes[0][2])["id"]

        # Roles track markers such as prerequisites/results while text is grouped within sections.
        roles = {}
        tables_by_page = {}
        for n, ls in page_lines.items():
            p = d[n - 1]
            floor = page_floor(p, cfg["profile"])
            for l in ls:
                rid = stable(key, "line", n, l["bbox"], f"{l['block']}:{l['line']}")
                self.raw.append(
                    dict(
                        id=rid,
                        **l,
                        source=loc(key, n, l["bbox"]),
                        excluded=l["bbox"][1] < floor[0] or l["bbox"][1] > floor[1],
                    )
                )
            tables = geometry_tables(p, ls) if cfg["profile"] == "hana" else []
            tables_by_page[n] = []
            for ti, t in enumerate(tables):
                o = self.add(
                    key,
                    "table",
                    "",
                    n,
                    t["bbox"],
                    parent(n, t["bbox"][1]),
                    **{k: v for k, v in t.items() if k != "bbox"},
                )
                o["bbox"] = t["bbox"]
                o["text"] = "\n".join(
                    [" | ".join(t["headers"])]
                    + [" | ".join(r["cells"]) for r in t["rows"]]
                )
                o["asset"] = self.crop(p, t["bbox"], o["id"])
                self.tables.append(o)
                tables_by_page[n].append(o)
                if t["needs_review"]:
                    self.issue(
                        "table_header_missing",
                        o,
                        "No multi-column header found; do not infer headers silently.",
                    )
                for ri, row in enumerate(t["rows"]):
                    r = self.add(
                        key,
                        "table_row",
                        " | ".join(row["cells"]),
                        n,
                        row["bbox"],
                        o["id"],
                        cells=row["cells"],
                        headers=t["headers"],
                        ordinal=ri + 1,
                    )
                    if t["headers"] and tidy(t["headers"][0]) == "Key":
                        r["exact_key"] = "".join(row["cells"][0].split())
                    if any("\n" in v for v in row["cells"]):
                        r["normalization_status"] = "raw_line_breaks_preserved"
            # Figures: actual large image regions, exclude icons/logos, keep caption linkage explicit.
            for im in p.get_image_info():
                r = pdf.Rect(im["bbox"])
                if r.width < 100 or r.height < 55 or r.y0 > floor[1]:
                    continue
                caps = [
                    l
                    for l in ls
                    if re.match(r"Figure \d+:", l["text"])
                    and r.y1 - 2 <= l["bbox"][1] <= r.y1 + 35
                ]
                caption = tidy(caps[0]["text"]) if caps else "Uncaptioned source figure"
                o = self.add(
                    key,
                    "figure",
                    caption,
                    n,
                    r,
                    parent(n, r.y0),
                    caption=caption,
                    visual_content_status="not_transcribed",
                )
                o["asset"] = self.crop(p, r, o["id"])
                o["caption_source"] = loc(key, n, caps[0]["bbox"]) if caps else None
                self.issue(
                    "figure_text_unextracted",
                    o,
                    "Image preserved; internal labels and relationships are not searchable yet.",
                )
            # Group original text blocks; tables are represented separately to avoid flattening their columns.
            blocks = collections.defaultdict(list)
            for l in ls:
                if floor[0] <= l["bbox"][1] <= floor[1]:
                    blocks[l["block"]].append(l)
            for _, bl in sorted(
                blocks.items(), key=lambda kv: min(l["bbox"][1] for l in kv[1])
            ):
                # Split block at table edges and heading/role boundaries.
                group = []
                for l in bl:
                    cy = (l["bbox"][1] + l["bbox"][3]) / 2
                    in_table = any(
                        pdf.Rect(t["bbox"]).contains(pdf.Point(l["bbox"][0] + 1, cy))
                        for t in tables
                    )
                    if in_table:
                        if group:
                            self.text_object(key, n, group, parent, roles)
                            group = []
                        continue
                    if group and (
                        parent(n, l["bbox"][1]) != parent(n, group[0]["bbox"][1])
                        or is_heading(l, cfg["profile"])
                        or is_heading(group[-1], cfg["profile"])
                    ):
                        self.text_object(key, n, group, parent, roles)
                        group = []
                    group.append(l)
                if group:
                    self.text_object(key, n, group, parent, roles)
        # Preserve PDF link annotations. External links remain references, never fetched.
        for n in page_lines:
            for link in d[n - 1].get_links():
                if "from" not in link:
                    continue
                r = link["from"]
                label = tidy(d[n - 1].get_textbox(r))
                self.add(
                    key,
                    "reference",
                    label,
                    n,
                    r,
                    parent(n, r.y0),
                    indexable_override=False,
                    target_uri=link.get("uri"),
                    target_pdf_page=(
                        link.get("page", -1) + 1 if link.get("page", -1) >= 0 else None
                    ),
                    target_named=link.get("nameddest"),
                    retrieved=False,
                )
        self.procedures(key)
        self.assessments(key)
        # Only join table fragments when source scope, headers and consecutive pages agree.
        ts = [t for t in self.tables if t["source"][0]["document_id"] == key]
        for a, b in zip(ts, ts[1:]):
            if (
                a["parent_id"] == b["parent_id"]
                and a["headers"] == b["headers"]
                and a["headers"]
                and b["source"][0]["pdf_page"] == a["source"][0]["pdf_page"] + 1
                and a["bbox"][3] > 650
                and b["bbox"][1] < 150
            ):
                a["continuation_ids"] = [b["id"]]
                b["continues_id"] = a["id"]
        self.figure_context(key)

    # Classify a text block using fonts, headings and its current section role; no LLM is called.
    def text_object(self, key, n, ls, parent, roles):
        txt = "\n".join(l["text"] for l in ls).strip()
        if not txt:
            return
        r = union([l["bbox"] for l in ls])
        pid = parent(n, r[1])
        compact = tidy(txt)
        typ = "paragraph"
        role = roles.get(pid, "body")
        if all(
            "Courier" in s["font"] for l in ls for s in l["spans"] if s["text"].strip()
        ):
            typ = "code"
        elif compact in {
            "LESSON OBJECTIVES",
            "UNIT OBJECTIVES",
            "LESSON SUMMARY",
            "LESSON OVERVIEW",
            "Prerequisites",
            "Context",
            "Procedure",
            "Results",
            "Related Information",
            "Example",
        }:
            typ = "heading"
            roles[pid] = compact.lower().replace(" ", "_")
            role = roles[pid]
        elif any(c.isalnum() for c in compact) and max(
            (
                s["size"]
                for l in ls
                for s in l["spans"]
                if any(c.isalnum() for c in s["text"])
            ),
            default=0,
        ) >= (11 if key.startswith("adm") else 12):
            typ = "heading"
            role = "body"
            roles[pid] = "body"
        elif re.match(r"^Figure \d+:", compact):
            typ = "caption"
        elif "objectives" in role:
            typ = "objective"
        elif role == "lesson_summary":
            typ = "summary"
        elif any("SAP-icons" in s["font"] for l in ls for s in l["spans"]):
            typ = "callout"
        o = self.add(key, typ, txt, n, r, pid, role=role)
        o["raw_line_ids"] = [
            stable(key, "line", n, l["bbox"], f"{l['block']}:{l['line']}") for l in ls
        ]

    # Collect numbered actions under their document parent, retaining IDs of the original step content.
    def procedures(self, key):
        source = [
            o
            for o in self.objects
            if o["source"][0]["document_id"] == key
            and o["type"]
            in {"paragraph", "code", "callout", "table", "figure", "heading"}
        ]
        byparent = collections.defaultdict(list)
        for o in source:
            byparent[o["parent_id"]].append(o)
        for pid, items in byparent.items():
            node = next(o for o in self.objects if o["id"] == pid)
            if "Learning Assessment" in node["text"]:
                continue
            items.sort(
                key=lambda o: (o["source"][0]["pdf_page"], o["source"][0]["bbox"][1])
            )
            explicit = any(o.get("role") == "procedure" for o in items)
            steps = []
            current = None
            active = False
            for o in items:
                if o["type"] == "heading":
                    if o.get("role") == "procedure":
                        active = True
                    elif tidy(o["text"]) in {
                        "Results",
                        "Related Information",
                        "Example",
                        "LESSON SUMMARY",
                    }:
                        active = False
                        current = None
                    continue
                m = re.match(r"^(\d+)\.\s", o["text"])
                # Numbers inside table cells never become procedure steps.
                if m and (active or not explicit):
                    current = dict(
                        number=int(m[1]), object_ids=[o["id"]], source=o["source"]
                    )
                    steps.append(current)
                elif current and (active or not explicit):
                    current["object_ids"].append(o["id"])
            if not steps:
                continue
            first = next(o for o in items if o["id"] == steps[0]["object_ids"][0])
            node = next(o for o in self.objects if o["id"] == pid)
            proc = self.add(
                key,
                "procedure",
                node["text"],
                first["source"][0]["pdf_page"],
                first["source"][0]["bbox"],
                pid,
                steps=steps,
                prerequisite_ids=[
                    o["id"]
                    for o in items
                    if o.get("role") == "prerequisites" and o["type"] != "heading"
                ],
                result_ids=[
                    o["id"]
                    for o in items
                    if o.get("role") == "results" and o["type"] != "heading"
                ],
                extraction_status="candidate_checked_numbering",
            )
            proc["source"] = [
                s
                for st in steps
                for oid in st["object_ids"]
                for obj in items
                if obj["id"] == oid
                for s in obj["source"]
            ]
            if [s["number"] for s in steps] != list(range(1, len(steps) + 1)):
                self.issue(
                    "procedure_numbering",
                    proc,
                    "Step sequence is incomplete or ambiguous.",
                )

    # Preserve assessment structure separately so raw checkbox choices are not treated as answer evidence.
    def assessments(self, key):
        if not key.startswith("adm"):
            return
        sections = [
            o
            for o in self.objects
            if o["type"] == "section"
            and o["source"][0]["document_id"] == key
            and "Learning Assessment" in o["text"]
        ]
        questions = {}
        for sec in sections:
            items = sorted(
                [
                    o
                    for o in self.objects
                    if o["parent_id"] == sec["id"]
                    and o["type"] not in {"section", "reference"}
                ],
                key=lambda o: (o["source"][0]["pdf_page"], o["source"][0]["bbox"][1]),
            )
            current = None
            for o in items:
                o["indexable"] = False  # raw checkbox text is not safe answer evidence
                m = re.match(r"^(\d+)\.\s", o["text"])
                if m:
                    current = int(m[1])
                    questions.setdefault(current, {})
                if current:
                    kind = "answer" if sec["text"].endswith("Answers") else "question"
                    questions[current].setdefault(kind, []).append(o)
        for num, pair in questions.items():
            q = pair.get("question", [])
            a = pair.get("answer", [])
            if not q:
                continue
            first = q[0]
            explanations = [o["text"] for o in a if "You are correct" in o["text"]]
            assessment = self.add(
                key,
                "assessment",
                "\n".join(o["text"] for o in q),
                first["source"][0]["pdf_page"],
                first["source"][0]["bbox"],
                sections[0]["parent_id"],
                question_number=num,
                answer_explanation="\n".join(explanations),
                answer_source=[s for o in a for s in o["source"]],
                question_object_ids=[o["id"] for o in q],
                answer_object_ids=[o["id"] for o in a],
                selected_options=None,
                status="paired_explanation_available_checkbox_selection_unverified",
            )
            assessment["source"] = [s for o in q for s in o["source"]]
            if not explanations:
                self.issue(
                    "assessment_answer_missing",
                    assessment,
                    "Answer explanation not found.",
                )
            self.issue(
                "assessment_checkbox_ambiguous",
                assessment,
                "Selected choices are deliberately unset: PDF text emits X for empty boxes too.",
            )

    # Attach nearby textual context to a figure; this does not recognize labels inside the image.
    def figure_context(self, key):
        for fig in [
            o
            for o in self.objects
            if o["type"] == "figure" and o["source"][0]["document_id"] == key
        ]:
            n = fig["source"][0]["pdf_page"]
            b = fig["source"][0]["bbox"]
            siblings = [
                o
                for o in self.objects
                if o["parent_id"] == fig["parent_id"]
                and o["type"] in {"paragraph", "caption", "figure"}
                and o["source"][0]["pdf_page"] == n
                and o["source"][0]["bbox"][1] >= b[3] - 1
            ]
            siblings.sort(key=lambda o: o["source"][0]["bbox"][1])
            ids = []
            for o in siblings:
                if o["type"] == "figure":
                    break
                ids.append(o["id"])
            fig["nearby_context_ids"] = ids

    # Save a source-image crop for review without claiming that its visual contents have been transcribed.
    def crop(self, page, bbox, oid):
        rel = "assets/" + oid.replace(":", "_") + ".png"
        page.get_pixmap(matrix=pdf.Matrix(1.5, 1.5), clip=pdf.Rect(bbox)).save(
            self.out / rel
        )
        return rel


# Edition-specific page boundaries exclude recurring headers and footers from normal body text.
def page_floor(page, profile):
    return (
        (65, page.rect.height - 60)
        if profile == "tadm"
        else (90, page.rect.height - 60)
    )


def is_heading(line, profile):
    return tidy(line["text"]) in {
        "LESSON OBJECTIVES",
        "UNIT OBJECTIVES",
        "LESSON SUMMARY",
        "LESSON OVERVIEW",
        "Prerequisites",
        "Context",
        "Procedure",
        "Results",
        "Related Information",
        "Example",
    } or (
        any(c.isalnum() for c in line["text"])
        and max(s["size"] for s in line["spans"]) >= (11 if profile == "tadm" else 12)
    )


# Check IDs, provenance and raw-line coverage. Structural completeness is not a semantic correctness score.
def validate(ex):
    ids = {o["id"] for o in ex.objects}
    raw = {o["id"] for o in ex.raw}
    errors = []
    if len(ids) != len(ex.objects):
        errors.append("Duplicate canonical IDs")
    for o in ex.objects:
        if o["parent_id"] and o["parent_id"] not in ids:
            errors.append("Dangling parent " + o["id"])
        if not o["source"]:
            errors.append("Missing provenance " + o["id"])
        for lid in o.get("raw_line_ids", []):
            if lid not in raw:
                errors.append("Dangling raw line " + lid)
        for st in o.get("steps", []):
            if any(i not in ids for i in st["object_ids"]):
                errors.append("Dangling step " + o["id"])
    # Coverage is source preservation, not a semantic correctness score.
    used = {x for o in ex.objects for x in o.get("raw_line_ids", [])}
    table_lines = set()
    for l in ex.raw:
        s = l["source"]
        p = pdf.Point(l["bbox"][0] + 1, (l["bbox"][1] + l["bbox"][3]) / 2)
        if any(
            t["source"][0]["document_id"] == s["document_id"]
            and t["source"][0]["pdf_page"] == s["pdf_page"]
            and pdf.Rect(t["bbox"]).contains(p)
            for t in ex.tables
        ):
            table_lines.add(l["id"])
    eligible = [l for l in ex.raw if not l["excluded"]]
    uncovered = [l["id"] for l in eligible if l["id"] not in used | table_lines]
    if uncovered:
        errors.append(f"{len(uncovered)} eligible text lines unassigned")
    return dict(
        errors=errors,
        canonical_objects=len(ex.objects),
        raw_lines=len(ex.raw),
        eligible_lines=len(eligible),
        assigned_lines=len(eligible) - len(uncovered),
        uncovered_line_ids=uncovered,
        types=dict(collections.Counter(o["type"] for o in ex.objects)),
        issue_counts=dict(collections.Counter(i["code"] for i in ex.issues)),
    )


# Render local HTML for human inspection of extracted tables, figures, procedures and warnings.
def render_review(ex, stats):
    def esc(x):
        return html.escape(str(x))

    byid = {o["id"]: o for o in ex.objects}
    parts = [
        '<!doctype html><meta charset="utf-8"><title>SAP Coach extraction review</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px}article{border-top:1px solid #bbb;padding:18px 0}pre{white-space:pre-wrap;background:#f4f5f7;padding:12px}img{max-width:100%;max-height:650px}small{color:#555}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:7px;vertical-align:top}code{overflow-wrap:anywhere}</style><h1>SAP Coach extraction review</h1><p>Candidate inventory. Image content is not transcribed; assessment choices are unset. No retrieval or answer generation has run.</p>',
        "<pre>" + esc(json.dumps(stats, indent=2)) + "</pre>",
    ]
    for o in ex.objects:
        if o["type"] not in {"section", "table", "figure", "procedure", "assessment"}:
            continue
        src = ", ".join(
            sorted(
                {
                    f"PDF {s['pdf_page']} / printed {s['printed_page']}"
                    for s in o["source"]
                }
            )
        )
        parts.append(
            f'<article id="{esc(o["id"])}"><h2>{esc(o["type"])}: {esc(o.get("title",o["text"][:100]))}</h2><small><code>{esc(o["id"])}</code> — {esc(src)}</small>'
        )
        if o.get("asset"):
            parts.append(f'<p><img loading="lazy" src="{esc(o["asset"])}"></p>')
        if o["type"] == "table":
            parts.append(
                "<table><tr>"
                + "".join("<th>" + esc(h) + "</th>" for h in o["headers"])
                + "</tr>"
            )
            for row in o["rows"]:
                parts.append(
                    "<tr>"
                    + "".join(
                        "<td>" + esc(c).replace("\n", "<br>") + "</td>"
                        for c in row["cells"]
                    )
                    + "</tr>"
                )
            parts.append("</table>")
        elif o["type"] == "procedure":
            for st in o["steps"]:
                parts.append(
                    "<h3>Step "
                    + str(st["number"])
                    + "</h3><pre>"
                    + esc("\n".join(byid[i]["text"] for i in st["object_ids"]))
                    + "</pre>"
                )
        elif o["type"] == "assessment":
            parts.append(
                "<pre>"
                + esc(o["text"] + "\nANSWER EXPLANATION:\n" + o["answer_explanation"])
                + "</pre>"
            )
        parts.append("</article>")
    (ex.out / "review.html").write_text("\n".join(parts))
