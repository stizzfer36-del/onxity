from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console()


def display_plan(plan: dict):
    t = Table(title="Plan")
    t.add_column("id")
    t.add_column("tool")
    t.add_column("requires")
    for s in plan.get("steps", []):
        t.add_row(
            s.get("id", ""),
            s.get("tool", ""),
            ",".join(s.get("requires", [])),
        )
    console.print(t)


def display_approval_prompt(token, details):
    console.print(
        f"[yellow]Approval required[/yellow] token={token} "
        f"details={details}"
    )


def display_audit_entry(entry):
    console.print(entry)
