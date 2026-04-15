"""
onxity.cli
==========
Main CLI entrypoint for onxity.

Quick-start / smoke test:
  # Interactive first-run wizard
  python -m onxity.cli first-run

  # Non-interactive (CI/dev)
  ONXITY_AUTO_APPROVE=true ONXITY_PROVIDER=mock python -m onxity.cli first-run --non-interactive

  # Launch REPL with mock provider
  ONXITY_PROVIDER=mock python -m onxity.cli repl

  # Absorb a plugin (dry-run)
  python -m onxity.cli absorb /path/to/plugin-repo

WARNING: --auto-approve is for CI/dev ONLY. It bypasses interactive prompts but
will NOT enable high-risk destructive scopes (execute, hardware, network) unless
additional unsafe flags are explicitly set and attested.
"""

import os
import sys

import click
from rich.console import Console

from onxity.config import load_config, save_config, default_config
from onxity.utils.display import display_plan, display_approval_prompt, display_audit_entry

console = Console()

AUTO_APPROVE = os.environ.get("ONXITY_AUTO_APPROVE", "").lower() in ("true", "1", "yes")


@click.group()
@click.version_option(package_name="onxity")
def main():
    """onxity — local-first agentic CLI OS."""
    pass


@main.command("first-run")
@click.option("--non-interactive", is_flag=True, default=False, help="Skip prompts; use env vars and defaults.")
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    envvar="ONXITY_AUTO_APPROVE",
    help="[DEV/CI ONLY] Auto-approve prompts. Does NOT enable high-risk scopes.",
)
def first_run(non_interactive: bool, auto_approve: bool):
    """
    Interactive first-run wizard that writes ~/.onxity/config.yaml.

    Non-interactive usage (CI/dev):
      ONXITY_AUTO_APPROVE=true ONXITY_PROVIDER=mock python -m onxity.cli first-run --non-interactive
    """
    cfg = default_config()

    # Override provider from env if set
    env_provider = os.environ.get("ONXITY_PROVIDER")
    if env_provider:
        cfg["provider"] = env_provider

    if not non_interactive:
        console.print("[bold cyan]Welcome to onxity first-run setup![/bold cyan]")
        provider_choice = click.prompt(
            "Provider [mock/anthropic/openai]",
            default=cfg["provider"],
        )
        cfg["provider"] = provider_choice

        console.print("[dim]Configuring permissions (safe defaults)...[/dim]")
        # Safe defaults — operator can edit config.yaml manually to expand
        console.print("[yellow]High-risk scopes (execute, hardware, network, fs:write) default to 'prompt'.[/yellow]")
    else:
        console.print("[dim]Non-interactive mode: writing defaults.[/dim]")

    if auto_approve:
        console.print(
            "[bold red]WARNING: --auto-approve active. Interactive prompts bypassed. "
            "High-risk scopes remain restricted.[/bold red]"
        )

    save_config(cfg)
    console.print(f"[green]Config written to {cfg['config_path']}[/green]")
    console.print("[bold]Run:[/bold] onxity repl")


@main.command("repl")
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    envvar="ONXITY_AUTO_APPROVE",
    help="[DEV/CI ONLY] Auto-approve all approval gates.",
)
def repl(auto_approve: bool):
    """Launch the interactive REPL."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style
    from onxity.config import load_config
    from onxity.providers.base import MockProvider
    from onxity.memory.buffer import RollingBuffer
    from onxity.core.agent import CeoAgent
    from onxity.core.orchestrator import Orchestrator
    from onxity.tools.registry import ToolRegistry
    from onxity.security.audit import AuditWriter

    cfg = load_config()
    provider_name = cfg.get("provider", "mock")

    if provider_name == "mock":
        provider = MockProvider()
    elif provider_name == "anthropic":
        from onxity.providers.anthropic import AnthropicProvider
        provider = AnthropicProvider(cfg)
    elif provider_name == "openai":
        from onxity.providers.openai import OpenAIProvider
        provider = OpenAIProvider(cfg)
    else:
        console.print(f"[red]Unknown provider: {provider_name}. Falling back to mock.[/red]")
        provider = MockProvider()

    memory = RollingBuffer(cfg)
    registry = ToolRegistry(cfg)
    audit = AuditWriter(cfg)
    agent = CeoAgent(id="ceo-001", provider=provider, memory=memory, config=cfg)
    orchestrator = Orchestrator(agent=agent, registry=registry, config=cfg, audit=audit)

    style = Style.from_dict({"prompt": "bold cyan"})
    session = PromptSession(style=style)

    console.print("[bold cyan]onxity REPL[/bold cyan] [dim](type 'exit' to quit)[/dim]")
    console.print(f"[dim]Provider: {provider_name} | DB: {cfg.get('db_path')}[/dim]")

    while True:
        try:
            user_input = session.prompt("onxity> ")
        except (EOFError, KeyboardInterrupt):
            console.print("[dim]Bye.[/dim]")
            break

        if user_input.strip().lower() in ("exit", "quit", "q"):
            console.print("[dim]Bye.[/dim]")
            break

        if not user_input.strip():
            continue

        try:
            plan = agent.plan(user_input)
            display_plan(plan)
            result = orchestrator.execute_plan(agent_id="ceo-001", plan=plan)
            synthesis = agent.synthesize(result.get("tool_results", []))
            console.print(f"[bold green]→[/bold green] {synthesis.get('final_message', '')")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")


@main.command("absorb")
@click.argument("repo_url_or_path")
def absorb(repo_url_or_path: str):
    """Absorb a plugin from a git repo URL or local path (dry-run by default)."""
    from onxity.plugins.absorb import AbsorbManager
    from onxity.config import load_config

    cfg = load_config()
    mgr = AbsorbManager(cfg)
    report = mgr.absorb(repo_url_or_path)
    console.print_json(data=report)

    if report.get("status") == "requires_approval":
        console.print(
            "[yellow]High-risk scopes detected. Run:[/yellow]\n"
            f"  onxity approve-plugin {report.get('absorb_id')} "
            "--attest \"<your legal attestation>\""
        )


@main.command("approve")
@click.argument("approval_token")
@click.option("--attest", default="", help="Legal attestation text. Required for high-risk scopes.")
def approve(approval_token: str, attest: str):
    """Approve a pending approval token."""
    from onxity.core.approval import ApprovalModule
    from onxity.config import load_config

    cfg = load_config()
    module = ApprovalModule(cfg)
    record = module.approve_token(approval_token, operator="cli-operator", attestation_text=attest)
    console.print(f"[green]Approved:[/green] {record}")


@main.command("approve-plugin")
@click.argument("absorb_id")
@click.option("--attest", required=True, help="Legal attestation text (required).")
def approve_plugin(absorb_id: str, attest: str):
    """Approve a plugin after absorb dry-run review."""
    from onxity.plugins.manager import PluginManager
    from onxity.config import load_config

    cfg = load_config()
    mgr = PluginManager(cfg)
    result = mgr.approve_plugin(absorb_id, attestation=attest)
    console.print(f"[green]Plugin enabled:[/green] {result}")


if __name__ == "__main__":
    main()
