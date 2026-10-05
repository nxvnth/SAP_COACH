"""From coach/: ../.venv/bin/python ingest.py --help."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coach.ingestion.pipeline import extract, build_index
from coach.settings import DOCUMENTS_DIR


# The CLI selects extraction or embedding; neither operation automatically changes the chatbot’s active index.
def main():
    parser = argparse.ArgumentParser(
        description="Extract PDFs or build a separate candidate index"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    extraction = commands.add_parser("extract")
    extraction.add_argument(
        "--sources",
        required=True,
        type=Path,
        help="JSON list of key/file/profile/start/end objects",
    )
    extraction.add_argument(
        "--output", required=True, type=Path, help="New candidate directory"
    )
    extraction.add_argument("--documents", type=Path, default=DOCUMENTS_DIR)
    indexing = commands.add_parser("build")
    indexing.add_argument("--dataset", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "extract":
        result = extract(
            json.loads(args.sources.read_text()), args.output, args.documents
        )
    else:
        result = build_index(args.dataset)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
