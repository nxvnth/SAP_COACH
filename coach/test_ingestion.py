"""Offline checks for the ingestion/retrieval handoff and overwrite protection."""

# READER GUIDE
# Tests for dataset boundaries rather than PDF extraction accuracy.
# Temporary files let these tests check tampering, model-identity mismatch,
# forbidden overwrites and source paths escaping the document directory.
# They do not exercise all layouts in the real SAP PDFs; source-specific
# extraction changes also need review of representative documents and tables.

import json
import tempfile
import unittest
from pathlib import Path
from .ingestion.pipeline import extract, build_index
from .retrieval.index_store import INDEX_FILES, write_manifest, validate_index


# Temporary datasets exercise integrity and overwrite guards without changing the active corpus.
class IngestionTests(unittest.TestCase):
    def test_manifest_detects_changed_assets_and_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in INDEX_FILES:
                (directory / name).write_bytes(b"example")
            config = {"model": "test", "revision": "one", "local_path": "models/old"}
            write_manifest(directory, config)
            validate_index(directory, dict(config, local_path="models/new"))
            with self.assertRaisesRegex(ValueError, "Embedding model changed"):
                validate_index(directory, dict(config, revision="two"))
            (directory / "inventory.json").write_text("modified")
            with self.assertRaisesRegex(ValueError, "integrity"):
                validate_index(directory, config)

    def test_existing_candidate_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "never overwritten"):
                extract([], Path(temporary))
            (Path(temporary) / "index_manifest.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                build_index(Path(temporary))

    def test_source_path_must_stay_in_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            documents = directory / "documents"
            documents.mkdir()
            (directory / "outside.pdf").write_bytes(b"not a pdf")
            with self.assertRaisesRegex(ValueError, "inside the documents"):
                extract(
                    [
                        dict(
                            key="test",
                            file="../outside.pdf",
                            profile="hana",
                            start=1,
                            end=1,
                        )
                    ],
                    directory / "candidate",
                    documents,
                )
            self.assertFalse((directory / "candidate").exists())

    def test_failed_extraction_cannot_be_indexed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "validation.json").write_text(
                json.dumps({"errors": ["Missing content"]})
            )
            with self.assertRaisesRegex(ValueError, "extraction errors"):
                build_index(directory)


if __name__ == "__main__":
    unittest.main()
