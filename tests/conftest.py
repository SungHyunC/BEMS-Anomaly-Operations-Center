import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make project root importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def tmp_db():
    """Point the store at a throwaway SQLite file for the test."""
    tmp = tempfile.NamedTemporaryFile(prefix="bems_test_", suffix=".sqlite3", delete=False)
    tmp.close()
    from src.agents import store as store_mod
    store_mod._store = store_mod.Store(path=tmp.name)
    yield store_mod._store
    store_mod._store.close()
    store_mod._store = None
    os.unlink(tmp.name)
