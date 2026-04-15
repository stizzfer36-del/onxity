from __future__ import annotations

from urllib.parse import urlparse

from git import Repo

from onxity.core.approval import ApprovalModule


def clone_dry_run(repo_url: str, target_dir: str) -> dict:
    u = urlparse(repo_url if "://" in repo_url else f"file://{repo_url}")
    needs_auth = bool(u.username or u.password) or repo_url.startswith("git@")
    return {"repo_url": repo_url, "target_dir": target_dir, "host": u.hostname or "local", "path": u.path, "needs_auth": needs_auth}


def clone_actual(config: dict, repo_url: str, target_dir: str, approved_token: str | None = None) -> dict:
    if not config.get("auto_approve") and not approved_token:
        token = ApprovalModule(config).create_approval_request("git", ["git"], f"clone {repo_url}", config["approval"]["token_expiry_seconds"])
        return {"status": "pending_approval", "approval_token": token}
    Repo.clone_from(repo_url, target_dir)
    return {"status": "ok", "target_dir": target_dir}
