"""Build reviewable candidate datasets. Never overwrite the active chat index."""

# READER GUIDE
# Offline orchestration: build a candidate, never mutate the live corpus.
# extract() takes source range dictionaries and writes objects, raw lines,
# source metadata, issues, validation results and an HTML review page.
# build_index() requires successful structural validation, makes passage windows,
# embeds them, and writes the index manifest last. It is a separate CLI operation
# so a person can inspect extraction before indexing.
# This is replacement-corpus construction, not incremental merging into the
# active index. A valid candidate becomes active only through explicit dataset
# selection and a server restart; neither function changes chat configuration.

import json
from pathlib import Path
import numpy as np
from .extractor import Extractor, validate, render_review, write_json
from .procedures import normalize_procedures
from ..retrieval.vector import load_model
from .chunking import passages
from ..retrieval.index_store import write_manifest
from ..settings import DOCUMENTS_DIR, DATASET_DIR


# Parse configured PDF ranges into a new reviewable dataset; this does not activate it for chat.
def extract(sources, output, documents_dir=DOCUMENTS_DIR):
    output = Path(output).resolve()
    if output == DATASET_DIR.resolve() or output.exists():
        raise ValueError(
            "Choose a new candidate directory; existing datasets are never overwritten"
        )
    # Resolve paths before checking them so ../ segments or symlinks cannot escape the input directory.
    documents_dir = Path(documents_dir).resolve()
    for source in sources:
        path = (documents_dir / source["file"]).resolve()
        if not path.is_relative_to(documents_dir) or not path.is_file():
            raise ValueError("Source PDF must exist inside the documents directory")
        if (
            source["profile"] not in {"tadm", "hana"}
            or not 1 <= source["start"] <= source["end"]
        ):
            raise ValueError(
                "Use a supported profile and a valid inclusive PDF page range"
            )
    output.mkdir(parents=True)
    extraction = Extractor(output, documents_dir)
    # Each range has its own outline/procedure state. Shared objects are deduplicated.
    for source in sources:
        part = Extractor(output, documents_dir)
        part.process(source)
        for attribute in ("objects", "raw", "manifest", "issues", "tables"):
            getattr(extraction, attribute).extend(getattr(part, attribute))
    for attribute in ("objects", "raw", "tables"):
        records = getattr(extraction, attribute)
        setattr(
            extraction,
            attribute,
            list({record["id"]: record for record in records}.values()),
        )
    # Separate restarted numbering into candidate procedures while preserving original source references.
    normalize_procedures(extraction, set())
    for obj in extraction.objects:
        if obj["type"] in {"table", "table_row"} and not obj.get("headers"):
            obj["indexable"] = False
    # Save diagnostics and the review page even if validation later rejects the dataset.
    stats = validate(extraction)
    for name, value in [
        ("inventory", extraction.objects),
        ("raw_lines", extraction.raw),
        ("manifest", extraction.manifest),
        ("issues", extraction.issues),
        ("validation", stats),
    ]:
        write_json(output / f"{name}.json", value)
    render_review(extraction, stats)
    if stats["errors"]:
        raise ValueError(
            "Extraction validation failed; inspect validation.json and review.html"
        )
    return stats


# Embed a validated inventory. Extraction/review and index building are deliberately separate operations.
def build_index(directory):
    directory = Path(directory).resolve()
    if (
        directory == DATASET_DIR.resolve()
        or (directory / "index_manifest.json").exists()
    ):
        raise ValueError("Refusing to overwrite an active or already built index")
    validation = json.loads((directory / "validation.json").read_text())
    if validation["errors"]:
        raise ValueError("Resolve extraction errors before building the index")
    objects = json.loads((directory / "inventory.json").read_text())
    config, model = load_model()
    rows = passages(objects, model.tokenizer)
    if not rows:
        raise ValueError("No indexable passages were extracted")
    # Use the same normalized embedding representation expected by online cosine search.
    vectors = model.encode(
        [row["text"] for row in rows],
        batch_size=16,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    if (
        vectors.shape != (len(rows), config["dimensions"])
        or not np.isfinite(vectors).all()
    ):
        raise ValueError("Invalid embedding output")
    write_json(directory / "passages.json", rows)
    np.save(directory / "vectors.npy", vectors)
    # Write the handoff manifest last; a partial build must not look like a completed index.
    write_manifest(directory, config)
    return {"passages": len(rows), "dimensions": vectors.shape[1]}
