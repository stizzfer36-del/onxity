from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import yaml

from onxity.packs.manifest import manifest_from_report, sign_manifest
from onxity.packs.registry import PackRegistry
from onxity.security.audit import AuditWriter
from onxity.tools.code.git import clone_dry_run

HIGH_RISK = {"execute", "network", "hardware", "spawn"}
SUSPICIOUS = ["subprocess", "scapy", "pyshark", "os.exec", "socket.SOCK_RAW", "requests.get(", "urllib.request"]


def _scan_python_files(root: Path) -> list[dict]:
    findings = []
    for file in root.rglob("*.py"):
        txt = file.read_text(encoding="utf-8", errors="ignore")
        for s in SUSPICIOUS:
            if s in txt:
                findings.append({"file": str(file), "pattern": s})
    if (root / "scripts" / "install.sh").exists():
        findings.append({"file": str(root / "scripts/install.sh"), "pattern": "install_script"})
    return findings


def _classify_repo(staging: Path) -> dict:
    if (staging / "pyproject.toml").exists() or list(staging.rglob("*.py")):
        lang = "python"
        runtime = "python>=3.11"
    elif list(staging.rglob("*.cs")):
        lang = "dotnet"
        runtime = "dotnet"
    else:
        lang = "unknown"
        runtime = "unknown"

    license_name = "unknown"
    for lf in ["LICENSE", "LICENSE.md", "COPYING"]:
        p = staging / lf
        if p.exists():
            license_name = p.read_text(encoding="utf-8", errors="ignore").splitlines()[0][:80] or "present"
            break
    return {"language": lang, "runtime": runtime, "license": license_name}


def _entrypoints(staging: Path) -> list[str]:
    candidates = []
    for p in [staging / "pyproject.toml", staging / "setup.py", staging / "main.py"]:
        if p.exists():
            candidates.append(str(p.relative_to(staging)))
    for p in staging.rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if "if __name__ == \"__main__\"" in txt:
            candidates.append(str(p.relative_to(staging)))
    return sorted(set(candidates))


def _infer_tools(manifest: dict) -> list[dict]:
    wrapped = []
    for t in manifest.get("tools", []):
        wrapped.append({
            "name": t.get("name"),
            "scopes": t.get("scopes", []),
            "adapter": f"pack_adapter::{t.get('name')}",
        })
    return wrapped


def _score(high_risk: list[str], findings: list[dict], tool_count: int) -> dict:
    usefulness = min(100, 40 + tool_count * 10)
    overlap = max(0, 100 - tool_count * 7)
    risk = min(100, len(high_risk) * 20 + len(findings) * 10)
    maintainability = max(0, 85 - len(findings) * 6)
    return {
        "usefulness": usefulness,
        "overlap": overlap,
        "risk": risk,
        "maintainability": maintainability,
        "recommended": risk < 70 and usefulness >= 50,
    }


def absorb_plugin(config: dict, repo_url_or_path: str) -> dict:
    """Serious absorption pipeline: quarantine -> classify -> scan -> stage signed pack."""
    audit = AuditWriter(config)
    plugin_root = Path(config["onxity_plugin_dir"]).expanduser()
    quarantine_root = plugin_root / "quarantine"
    plugin_root.mkdir(parents=True, exist_ok=True)
    quarantine_root.mkdir(parents=True, exist_ok=True)

    absorb_id = f"absorb-{hashlib.sha1(repo_url_or_path.encode()).hexdigest()[:8]}"
    staging = quarantine_root / absorb_id
    dry = clone_dry_run(repo_url_or_path, str(staging))

    if Path(repo_url_or_path).exists():
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(repo_url_or_path, staging)

    manifest_path = staging / "onxity_plugin.yaml"
    if not manifest_path.exists():
        audit.append("absorb", {"absorb_id": absorb_id, "status": "manifest_missing", "dry_run": dry})
        return {"status": "manifest_missing", "absorb_id": absorb_id, "dry_run": dry}

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    scopes = [scope for t in manifest.get("tools", []) for scope in t.get("scopes", [])]
    high = sorted(set(scopes) & HIGH_RISK)
    findings = _scan_python_files(staging)
    classification = _classify_repo(staging)
    entrypoints = _entrypoints(staging)
    wrapped_tools = _infer_tools(manifest)
    score = _score(high, findings, len(wrapped_tools))

    pipeline_status = "requires_approval" if high or findings else "ready_for_stage"
    report = {
        "status": pipeline_status,
        "absorb_id": absorb_id,
        "source": repo_url_or_path,
        "dry_run": dry,
        "quarantine_path": str(staging),
        "classification": classification,
        "entrypoints": entrypoints,
        "manifest": manifest,
        "declared_high_risk_scopes": high,
        "suspicious_imports": findings,
        "wrapped_tools": wrapped_tools,
        "score": score,
        "required_steps": [
            "manual_review",
            "sandbox_test",
            "legal_attestation",
            "explicit_enable",
        ],
    }

    pack_manifest = manifest_from_report(report).to_dict()
    signature = sign_manifest(pack_manifest, config.get("pack_signing_secret", "dev-secret"))
    staged = PackRegistry(config).stage(pack_manifest, signature)
    report["pack_manifest"] = pack_manifest
    report["pack_signature"] = signature
    report["stage"] = staged

    audit.append("absorb", report)
    return report
