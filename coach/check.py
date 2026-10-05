"""Run the app's offline tests from inside this directory."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Run offline regression suites only; this entry point does not submit paid model requests.
if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromNames(
        ["coach.test_coach", "coach.test_ingestion"]
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
