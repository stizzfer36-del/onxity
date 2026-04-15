from __future__ import annotations

from pathlib import Path

import pytest

from onxity.config import default_config, save_config
from onxity.memory.sqlite_store import init_db
from onxity.providers.base import MockProvider


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def tmp_config(tmp_path: Path):
    cfg = default_config()
    cfg["audit_path"] = str(tmp_path / "audit.jsonl")
    cfg["db_path"] = str(tmp_path / "onxity.db")
    cfg["onxity_plugin_dir"] = str(tmp_path / "plugins")
    cfg["allowed_roots"] = [str(tmp_path)]
    p = tmp_path / "config.yaml"
    save_config(cfg, str(p))
    return cfg


@pytest.fixture
def in_memory_sqlite():
    init_db("sqlite:///:memory:")
    return True


class _MockCompressor:
    def complete(self, messages, tools):
        return {"content": "SUMMARY: " + messages[-1]["content"][:80]}


@pytest.fixture
def mock_compressor():
    return _MockCompressor()
