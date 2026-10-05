"""Versioned data contract between offline ingestion and online retrieval."""

# READER GUIDE
# The file-level handoff between ingestion and online search.
# An index consists of inventory.json (objects), manifest.json (source editions),
# passages.json (embedding windows/spans), and vectors.npy (one vector per window).
# index_manifest.json records their hashes plus the embedding configuration.
# Moving identical model files is allowed; changing model identity requires a
# rebuild. Hash checks detect changed artifacts, not incorrect extraction or
# unsupported claims. Human review and quality evaluation remain separate.

import hashlib
import json
from pathlib import Path

# These four files must travel together when promoting an index from ingestion to retrieval.
INDEX_FILES = ("inventory.json", "manifest.json", "passages.json", "vectors.npy")


def embedding_identity(config):
    """Disk location is deployment-specific; model revision and tokenization are not."""
    return {key: value for key, value in config.items() if key != "local_path"}


# Record model identity and exact artifact hashes after all candidate index files have been written.
def write_manifest(directory, config):
    directory = Path(directory)
    manifest = {
        "format_version": 1,
        "embedding": embedding_identity(config),
        "files": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in INDEX_FILES
        },
    }
    (directory / "index_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


# Fail before search if artifacts are modified or belong to a different embedding configuration.
def validate_index(directory, config):
    directory = Path(directory)
    manifest = json.loads((directory / "index_manifest.json").read_text())
    if manifest["format_version"] != 1:
        raise ValueError("Unsupported index format")
    if manifest["embedding"] != embedding_identity(config):
        raise ValueError("Embedding model changed: rebuild this index")
    for name in INDEX_FILES:
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if manifest["files"].get(name) != actual:
            raise ValueError(f"Index integrity check failed: {name}")
