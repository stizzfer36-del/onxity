from __future__ import annotations

from onxity.memory.buffer import RollingBuffer
from onxity.memory.sqlite_store import MemoryChunk, get_session


def test_compression_cycle(tmp_config, in_memory_sqlite, mock_compressor):
    cfg = tmp_config
    cfg["memory"]["max_items"] = 5
    b = RollingBuffer(cfg)
    for i in range(6):
        b.append({"ts": float(i), "msg": f"m{i}"})
    result = b.check_and_compress(mock_compressor)
    assert result["compressed"] is True
    db = get_session()
    assert db.query(MemoryChunk).count() == 1
    assert len(b.snapshot()) <= 5
