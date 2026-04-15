from __future__ import annotations

import json
from pathlib import Path

from onxity.packs.manifest import verify_manifest


class PackRegistry:
    def __init__(self, config: dict):
        self.path = Path(config["pack_registry_path"]).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.secret = config.get("pack_signing_secret", "dev-secret")
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.state = {"packs": {}, "enabled": {}}

    def save(self):
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def stage(self, manifest: dict, signature: str) -> dict:
        if not verify_manifest(manifest, signature, self.secret):
            return {"status": "denied", "reason": "invalid_signature"}
        pid = manifest["pack_id"]
        self.state["packs"][pid] = {"manifest": manifest, "signature": signature, "status": "staged"}
        self.save()
        return {"status": "staged", "pack_id": pid}

    def enable(self, pack_id: str) -> dict:
        if pack_id not in self.state["packs"]:
            return {"status": "error", "error": "unknown_pack"}
        self.state["enabled"][pack_id] = True
        self.state["packs"][pack_id]["status"] = "enabled"
        self.save()
        return {"status": "enabled", "pack_id": pack_id}
