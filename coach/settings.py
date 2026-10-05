"""All application paths are relative to this directory, not the parent project."""

import json
import os
from pathlib import Path

# Resolve assets relative to this package so starting the command from another directory still works.
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
# Credentials and the Python environment belong to the project root; app assets remain under coach/data.
ENV_FILE = PROJECT_DIR / ".env"
DOCUMENTS_DIR = APP_DIR / "data/documents"
# Set SAP_COACH_INDEX before startup to test a candidate dataset without replacing the default index.
DATASET_DIR = Path(os.environ.get("SAP_COACH_INDEX", str(APP_DIR / "data/index")))
# Mutable caches and usage ledgers are separate from the source PDFs, models and searchable index.
STATE_DIR = Path(os.environ.get("SAP_COACH_STATE", str(APP_DIR / ".data")))
FRONTEND_DIR = APP_DIR / "web/dist"
MODEL_CONFIG = json.loads((APP_DIR / "config.json").read_text())
# These limits bound prompt history, not the number of turns retained in the in-memory thread.
HISTORY_MESSAGE_LIMIT = 12
HISTORY_CHARACTER_LIMIT = 16000
