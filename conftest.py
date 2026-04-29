"""Make the 'app' package importable from tests.

The repo doesn't ship a pyproject.toml because the demo runs as a
plain script. Adding this conftest.py at the repo root puts the
parent dir on sys.path so 'from app.chunking import ...' resolves
when pytest collects tests/test_*.py.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
