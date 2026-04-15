from __future__ import annotations

from git import Repo

from onxity.tools.registry import tool


@tool(name="git.status", description="Read git status", required_scopes=["git", "fs:read"])
def git_status(repo_path: str) -> dict:
    repo = Repo(repo_path)
    return {
        "branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED",
        "is_dirty": repo.is_dirty(untracked_files=True),
        "untracked": repo.untracked_files,
    }
