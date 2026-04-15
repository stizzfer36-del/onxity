"""onxity CLI.

Phase-1 quick start
- Interactive: `python -m onxity.cli first-run`
- Non-interactive: `ONXITY_AUTO_APPROVE=true ONXITY_PROVIDER=mock python -m onxity.cli first-run --non-interactive`
- REPL: `python -m onxity.cli repl`
- Smoke test: type `show /etc/issue` in REPL while provider is `mock`.

Safety notes
- `--auto-approve` is DEV/CI only.
- High-risk scopes are still prompt/deny by default and require explicit attestation for enablement.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from rich.console import Console

from onxity.config import default_config, load_config, save_config
from onxity.core.agent import CeoAgent
from onxity.core.approval import ApprovalModule
from onxity.core.orchestrator import Orchestrator
from onxity.memory.buffer import RollingBuffer
from onxity.plugins.absorb import absorb_plugin
from onxity.providers.anthropic import AnthropicProvider
from onxity.providers.base import MockProvider
from onxity.providers.openai import OpenAIProvider
from onxity.tools.registry import ToolRegistry
from onxity.tools.system.filesystem import filesystem_find, filesystem_read, filesystem_write
from onxity.utils.display import display_approval_prompt, display_plan

console = Console()


def _provider_from_cfg(cfg: dict):
    p = cfg.get("provider", "mock")
    if p == "mock":
        return MockProvider()
    if p == "anthropic":
        return AnthropicProvider(cfg)
    if p == "openai":
        return OpenAIProvider(cfg)
    return MockProvider()


@click.group()
def main() -> None:
    """onxity local-first CLI."""


@main.command("first-run")
@click.option("--non-interactive", is_flag=True)
@click.option("--auto-approve", is_flag=True, envvar="ONXITY_AUTO_APPROVE", help="DEV-only.")
def first_run(non_interactive: bool, auto_approve: bool) -> None:
    cfg = default_config()
    if os.getenv("ONXITY_PROVIDER"):
        cfg["provider"] = os.environ["ONXITY_PROVIDER"]
    if not non_interactive:
        cfg["provider"] = click.prompt("Provider", default=cfg["provider"])
    cfg["auto_approve"] = bool(auto_approve)
    save_config(cfg)
    console.print(f"[green]Saved[/green] {cfg['config_path']}")


@main.command("repl")
@click.option("--auto-approve", is_flag=True, envvar="ONXITY_AUTO_APPROVE")
def repl(auto_approve: bool) -> None:
    cfg = load_config()
    cfg["auto_approve"] = bool(auto_approve or cfg.get("auto_approve"))
    provider = _provider_from_cfg(cfg)
    memory = RollingBuffer(cfg)
    registry = ToolRegistry(cfg)
    registry.register(filesystem_read)
    registry.register(filesystem_write)
    registry.register(filesystem_find)
    agent = CeoAgent(id="ceo", provider=provider, memory=memory, config=cfg)
    orch = Orchestrator(agent=agent, registry=registry, config=cfg)

    session = PromptSession("onxity> ")
    while True:
        try:
            text = session.prompt()
        except (EOFError, KeyboardInterrupt):
            break
        if text.strip().lower() in {"exit", "quit"}:
            break
        plan = agent.plan(text)
        display_plan(plan)
        result = orch.execute_plan("ceo", plan)
        if result.get("status") == "pending_approval":
            display_approval_prompt(result["approval_token"], result)
            continue
        synthesis = agent.synthesize(result.get("tool_results", []))
        console.print(synthesis["final_message"])


@main.command("absorb")
@click.argument("repo")
def absorb(repo: str) -> None:
    cfg = load_config()
    report = absorb_plugin(cfg, repo)
    console.print_json(data=report)


@main.command("approve")
@click.argument("approval_token")
@click.option("--attest", default="")
def approve(approval_token: str, attest: str) -> None:
    cfg = load_config()
    mod = ApprovalModule(cfg)
    record = mod.approve_token(approval_token, operator=os.getenv("USER", "operator"), attestation_text=attest)
    console.print_json(data=record)


if __name__ == "__main__":
    main()
