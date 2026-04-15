from __future__ import annotations

from onxity.packs.manifest import sign_manifest
from onxity.packs.registry import PackRegistry


def test_pack_stage_and_enable(tmp_config):
    reg = PackRegistry(tmp_config)
    manifest = {
        "pack_id": "absorb-test",
        "version": "0.1.0",
        "source": "local",
        "language": "python",
        "runtime": "python",
        "license": "MIT",
        "entrypoints": ["main.py"],
        "tools": [],
        "risk_findings": [],
        "score": {"risk": 0},
        "created_ts": 0,
    }
    sig = sign_manifest(manifest, tmp_config["pack_signing_secret"])
    stage = reg.stage(manifest, sig)
    assert stage["status"] == "staged"
    enabled = reg.enable("absorb-test")
    assert enabled["status"] == "enabled"
