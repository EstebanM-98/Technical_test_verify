import json
import os
import sys
import tempfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LOG_DIR", tempfile.mkdtemp(prefix="pytest-logs-"))

FRONTEND_ROOT = ROOT / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))


@pytest.fixture
def fixtures_dir() -> Path:
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def read_fixture_text(fixtures_dir):
    def _reader(name: str) -> str:
        return (fixtures_dir / name).read_text(encoding="utf-8")

    return _reader


@pytest.fixture
def read_fixture_json(fixtures_dir):
    def _reader(name: str) -> dict:
        with (fixtures_dir / name).open("r", encoding="utf-8") as f:
            return json.load(f)

    return _reader
