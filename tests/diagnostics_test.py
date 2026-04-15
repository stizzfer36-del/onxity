from __future__ import annotations

from onxity.diagnostics import collect_diagnostics


def test_collect_diagnostics_has_required_fields(tmp_config):
    data = collect_diagnostics()
    for key in [
        "os",
        "python",
        "repo_root",
        "config_path",
        "runtime_state_path",
        "onxity_importable",
        "paths_writable",
    ]:
        assert key in data
    assert isinstance(data["paths_writable"], dict)
