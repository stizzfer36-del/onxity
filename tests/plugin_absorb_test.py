from __future__ import annotations

from pathlib import Path

import yaml

from onxity.plugins.absorb import absorb_plugin


def test_absorb_dry_run_flags(tmp_config, tmp_path: Path):
    repo = tmp_path / "plugin"
    repo.mkdir()
    (repo / "mod.py").write_text("import subprocess\nimport scapy\n")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "install.sh").write_text("#!/bin/sh\n")
    manifest = {
        "id": "sample-plugin",
        "name": "Sample",
        "version": "0.1.0",
        "tools": [{"name": "wifi_scan", "scopes": ["network", "hardware", "execute"]}],
    }
    (repo / "onxity_plugin.yaml").write_text(yaml.safe_dump(manifest))
    report = absorb_plugin(tmp_config, str(repo))
    assert report["status"] == "requires_approval"
    assert "execute" in report["declared_high_risk_scopes"]
    pats = {f['pattern'] for f in report['suspicious_imports']}
    assert "subprocess" in pats and "scapy" in pats
