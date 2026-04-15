from __future__ import annotations

import json
from pathlib import Path

from onxity.security.audit import AuditWriter


class PluginManager:
    def __init__(self, config: dict):
        self.cfg = config
        self.root = Path(config["onxity_plugin_dir"]).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_file = self.root / "state.json"
        self.audit = AuditWriter(config)
        if self.state_file.exists():
            self.state = json.loads(self.state_file.read_text())
        else:
            self.state = {"installed": {}, "enabled": {}}

    def _save(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def list_installed(self):
        return self.state["installed"]

    def enable(self, plugin_id):
        self.state["enabled"][plugin_id] = True
        self._save()

    def disable(self, plugin_id):
        self.state["enabled"][plugin_id] = False
        self._save()

    def load_plugin(self, plugin_dir: str):
        p = Path(plugin_dir)
        manifest = p / "onxity_plugin.yaml"
        if not manifest.exists():
            raise ValueError("missing manifest")
        return manifest

    def approve_plugin(self, absorb_id: str, attestation: str):
        self.audit.append("plugin_approval", {"absorb_id": absorb_id, "attestation": attestation})
        self.enable(absorb_id)
        return {"plugin_id": absorb_id, "enabled": True}
