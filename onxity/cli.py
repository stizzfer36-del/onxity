"""onxity CLI - local-first operator shell and runtime management."""

from __future__ import annotations

import os
import subprocess
import sys

import click
from prompt_toolkit import PromptSession
from rich.console import Console

from onxity.agency.team import TeamOrchestrator
from onxity.config import default_config, load_config, save_config
from onxity.core.agent import CeoAgent
from onxity.core.approval import ApprovalModule
from onxity.core.orchestrator import Orchestrator
from onxity.diagnostics import collect_diagnostics
from onxity.embodiment.browser import browser_fetch
from onxity.embodiment.git_tools import git_status
from onxity.embodiment.host import host_health, process_list
from onxity.embodiment.terminal import terminal_exec
from onxity.kernel.daemon import OnxityDaemon
from onxity.kernel.events import EventBus
from onxity.kernel.identity import IdentityStore
from onxity.kernel.state import RuntimeState
from onxity.memory.buffer import RollingBuffer
from onxity.memory.sqlite_store import init_db
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


def _build_runtime(cfg: dict):
    init_db(f"sqlite:///{cfg['db_path']}")
    provider = _provider_from_cfg(cfg)
    memory = RollingBuffer(cfg)
    registry = ToolRegistry(cfg)
    for fn in [filesystem_read, filesystem_write, filesystem_find, host_health, process_list, terminal_exec, git_status, browser_fetch]:
        registry.register(fn)
    agent = CeoAgent(id="ceo", provider=provider, memory=memory, config=cfg)
    events = EventBus()
    orch = Orchestrator(agent=agent, registry=registry, config=cfg, event_bus=events)
    team = TeamOrchestrator(cfg)
    return agent, orch, team


def _handle_operator_turn(text: str, agent: CeoAgent, orch: Orchestrator, team: TeamOrchestrator) -> None:
    plan = agent.plan(text)
    display_plan(plan)
    worker = team.spawn_worker("worker-main", "ceo", depth=1, scopes=[s for st in plan.get("steps", []) for s in st.get("requires", [])])
    if worker.get("status") != "ok":
        console.print_json(data=worker)
        return
    result = orch.execute_plan("ceo", plan)
    verify = team.verify_result("worker-main", result)
    if verify["verdict"] == "needs_recovery":
        console.print_json(data=team.recovery_plan("worker-main", result))
        return
    if result.get("status") == "pending_approval":
        display_approval_prompt(result["approval_token"], result)
        return
    synthesis = agent.synthesize(result.get("tool_results", []))
    console.print(synthesis["final_message"])


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
    identity = IdentityStore(cfg).load_or_create()
    console.print(f"[green]Saved[/green] {cfg['config_path']}")
    console.print(f"Operator identity: {identity['operator_id']}")


@main.command("doctor")
def doctor() -> None:
    """Print local environment diagnostics for troubleshooting."""
    console.print_json(data=collect_diagnostics())


@main.command("daemon-start")
def daemon_start() -> None:
    cfg = load_config()
    status = OnxityDaemon.read_status(cfg)
    if status.get("state", {}).get("running") and status.get("pid"):
        console.print_json(data={"status": "already_running", "pid": status["pid"]})
        return
    if os.getenv("ONXITY_DAEMON_FOREGROUND") == "1":
        OnxityDaemon(cfg).run_foreground()
        return
    cmd = [sys.executable, "-m", "onxity.cli", "daemon-start"]
    env = os.environ.copy()
    env["ONXITY_DAEMON_FOREGROUND"] = "1"
    cp = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    console.print_json(data={"status": "started", "pid": cp.pid})


@main.command("daemon-stop")
def daemon_stop() -> None:
    cfg = load_config()
    console.print_json(data=OnxityDaemon.stop_existing(cfg))


@main.command("daemon-status")
def daemon_status() -> None:
    cfg = load_config()
    console.print_json(data=OnxityDaemon.read_status(cfg))


@main.command("repl")
@click.option("--auto-approve", is_flag=True, envvar="ONXITY_AUTO_APPROVE")
def repl(auto_approve: bool) -> None:
    cfg = load_config()
    cfg["auto_approve"] = bool(auto_approve or cfg.get("auto_approve"))
    RuntimeState(cfg).start_session("ceo", {"surface": "repl"})
    agent, orch, team = _build_runtime(cfg)

    if not sys.stdin.isatty():
        for raw in sys.stdin:
            text = raw.strip()
            if text.lower() in {"exit", "quit"}:
                break
            if text:
                _handle_operator_turn(text, agent, orch, team)
        return

    session = PromptSession("onxity> ")
    while True:
        try:
            text = session.prompt()
        except (EOFError, KeyboardInterrupt):
            break
        if text.strip().lower() in {"exit", "quit"}:
            break
        _handle_operator_turn(text, agent, orch, team)


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
    try:
        record = mod.approve_token(approval_token, operator=os.getenv("USER", "operator"), attestation_text=attest)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print_json(data=record)


if __name__ == "__main__":
    main()
