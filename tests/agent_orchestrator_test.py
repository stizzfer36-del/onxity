from __future__ import annotations

import queue

from onxity.core.agent import CeoAgent
from onxity.core.orchestrator import Orchestrator
from onxity.core.subagent import SubAgent
from onxity.memory.buffer import RollingBuffer
from onxity.memory.sqlite_store import init_db
from onxity.providers.base import MockProvider
from onxity.tools.registry import ToolRegistry
from onxity.tools.system.filesystem import filesystem_read


def test_example1_safe_read_flow(tmp_config, tmp_path):
    init_db("sqlite:///:memory:")
    p = tmp_path / "issue"
    p.write_text("hello-issue")
    agent = CeoAgent(
        "ceo",
        MockProvider(),
        RollingBuffer(tmp_config),
        tmp_config,
    )
    reg = ToolRegistry(tmp_config)
    reg.register(filesystem_read)
    plan = agent.plan(f"show {p}")
    orch = Orchestrator(agent, reg, tmp_config)
    out = orch.execute_plan("ceo", plan)
    synth = agent.synthesize(out["tool_results"])
    assert "hello-issue" in synth["final_message"]


def test_subagent_depth_limit(tmp_config):
    q = queue.Queue()
    s = SubAgent(
        "sub1",
        ["filesystem.read"],
        max_depth=1,
        parent_id="ceo",
        task_queue=q,
        config=tmp_config,
        depth=1,
    )
    assert s.spawn_allowed() is False


def test_plan_validation_proof_required(tmp_config):
    class BadProvider(MockProvider):
        def complete(self, messages, tools):
            return {
                "content": (
                    '{"steps":[{"id":"x","action":"n","tool":'
                    '"network.fetch","args":{},"requires":'
                    '["network"],"proof_required":true}]}'
                )
            }

    a = CeoAgent("ceo", BadProvider(), RollingBuffer(tmp_config), tmp_config)
    import pytest

    with pytest.raises(Exception):
        a.plan("fetch cve")
