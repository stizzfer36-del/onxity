from __future__ import annotations

import sys

from onxity.tools.code.executor import execute


def test_executor_timeout():
    res = execute([sys.executable, "-c", "import time; time.sleep(10)"], timeout=2, cpu_seconds=1, max_open_files=64)
    assert res["timed_out"] is True
    assert res["exit_code"] is None


def test_executor_short_script():
    res = execute([sys.executable, "-c", "print('ok')"], timeout=2)
    assert res["timed_out"] is False
    assert "ok" in res["stdout"]
