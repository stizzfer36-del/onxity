from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import yaml

from onxity.security.audit import AuditWriter
from onxity.tools.code.git import clone_dry_run

HIGH_RISK = {"execute", "network", "hardware", "spawn"}
SUSPICIOUS = ["subprocess", "scapy", "pyshark", "os.exec", "socket.SOCK_RAW"]


def _scan_python_files(root: Path) -> list[dict]:
    findings = []
    for file in root.rglob("*.py"):
        txt = file.read_text(encoding="utf-8", errors="ignore")
        for s in SUSPICIOUS:
            if s in txt:
                findings.append({"file": str(file), "pattern": s})
    if (root / "scripts" / "install.sh").exists():
        findings.append({"file": str(root / 'scripts/install.sh'), "pattern": "install_script"})
    return findings


def absorb_plugin(config: dict, repo_url_or_path: str) -> dict:
    audit = AuditWriter(config)
    plugin_root = Path(config["onxity_plugin_dir"]).expanduser()
    plugin_root.mkdir(parents=True, exist_ok=True)
    absorb_id = f"absorb-{hashlib.sha1(repo_url_or_path.encode()).hexdigest()[:8]}"
    staging = plugin_root / absorb_id
    dry = clone_dry_run(repo_url_or_path, str(staging))
    if Path(repo_url_or_path).exists():
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(repo_url_or_path, staging)
    manifest_path = staging / "onxity_plugin.yaml"
    if not manifest_path.exists():
        audit.append("absorb_dry_run", {"absorb_id": absorb_id, "status": "manifest_missing", "dry_run": dry})
        return {"status": "manifest_missing", "absorb_id": absorb_id, "dry_run": dry}
    manifest = yaml.safe_load(manifest_path.read_text())
    scopes = []
    for t in manifest.get("tools", []):
        scopes.extend(t.get("scopes", []))
    high = sorted(set(scopes) & HIGH_RISK)
    findings = _scan_python_files(staging)
    status = "requires_approval" if high or findings else "ok"
    report = {
        "status": status,
        "absorb_id": absorb_id,
        "dry_run": dry,
        "manifest": manifest,
        "declared_high_risk_scopes": high,
        "suspicious_imports": findings,
        "required_steps": ["manual_review", "legal_attestation", "explicit_enable"],
    }
    audit.append("absorb_dry_run", report)
    return report
