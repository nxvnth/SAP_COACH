"""Offline packaging check: copy the app alone, then load UI, PDF and retrieval."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# Copy only app-owned files and verify them in another directory with no experiment folders available.
def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="sap-coach-isolation-") as temporary:
        target = Path(temporary) / "coach"
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns(
                ".data", ".smoke*", "__pycache__", "node_modules", ".venv", ".env"
            ),
        )
        script = """
import runpy, sys
from pathlib import Path
from fastapi.testclient import TestClient
app = runpy.run_path('run.py', run_name='packaging_check')['app']
from coach.retrieval import Retriever
from coach.settings import APP_DIR, DATASET_DIR
assert APP_DIR.resolve() == Path.cwd().resolve()
client = TestClient(app)
assert client.get('/api/health').status_code == 200
assert client.get('/').status_code == 200
assert client.get('/api/documents/adm328-v23').status_code == 200
retriever = Retriever()
retriever.initialize()
hits, *_ = retriever.engine.search('What does Maintenance Planner do?')
assert hits
retriever.engine.close()
for name, module in list(sys.modules.items()):
    if name == 'coach' or name.startswith('coach.'):
        if getattr(module, '__file__', None):
            assert Path(module.__file__).resolve().is_relative_to(APP_DIR.resolve())
print('Isolated app: UI, health, PDF and local search passed; all coach modules loaded from the copied app.')
"""
        subprocess.run([sys.executable, "-c", script], cwd=target, check=True)


if __name__ == "__main__":
    main()
