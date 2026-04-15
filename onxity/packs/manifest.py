from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass


@dataclass
class PackManifest:
    pack_id: str
    version: str
    source: str
    language: str
    runtime: str
    license: str
    entrypoints: list[str]
    tools: list[dict]
    risk_findings: list[dict]
    score: dict
    created_ts: float

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "version": self.version,
            "source": self.source,
            "language": self.language,
            "runtime": self.runtime,
            "license": self.license,
            "entrypoints": self.entrypoints,
            "tools": self.tools,
            "risk_findings": self.risk_findings,
            "score": self.score,
            "created_ts": self.created_ts,
        }


def sign_manifest(manifest: dict, secret: str) -> str:
    payload = json.dumps(manifest, sort_keys=True).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_manifest(manifest: dict, signature: str, secret: str) -> bool:
    return hmac.compare_digest(sign_manifest(manifest, secret), signature)


def manifest_from_report(report: dict) -> PackManifest:
    return PackManifest(
        pack_id=report["absorb_id"],
        version="0.1.0",
        source=report["source"],
        language=report["classification"]["language"],
        runtime=report["classification"]["runtime"],
        license=report["classification"]["license"],
        entrypoints=report["entrypoints"],
        tools=report["wrapped_tools"],
        risk_findings=report["suspicious_imports"],
        score=report["score"],
        created_ts=time.time(),
    )
