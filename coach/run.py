"""Run with `python run.py` from inside coach/, or `python coach/run.py`."""

# READER GUIDE
# Local application entry point: from coach run ../.venv/bin/python run.py.
# The import-path adjustment exposes the coach package; it does not import
# experiments. Importing server creates routes/services; uvicorn serves them.
# Retrieval model loading is deferred until a question actually needs it.

import sys
from pathlib import Path
import uvicorn

# Make this package importable without requiring the parent project's code/assets.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coach.server import app

# Launching this file starts the local HTTP server; importing it only constructs the app.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
