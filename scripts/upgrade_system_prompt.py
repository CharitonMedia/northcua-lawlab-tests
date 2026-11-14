#!/usr/bin/env python3
"""Wire the existing intended Web prompt when callers haven't supplied a custom one."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"vendor/NorthCUA"
p=root/"northcua/agents/web/runner/model_step.py";s=p.read_text()
old='''    def _configure_agent_for_step(agent_config: AgentConfig) -> None:
        stop_tools = set(agent_config.stop_tools or set())'''
new='''    def _configure_agent_for_step(agent_config: AgentConfig) -> None:
        if not agent_config.system_prompt:
            agent_config.system_prompt = str(Path(__file__).resolve().parents[1] / "prompt/templates/web_agent_system.j2")
            agent_config.system_prompt_type = "jinja"
        stop_tools = set(agent_config.stop_tools or set())'''
assert old in s;s=s.replace(old,new);p.write_text(s)
print("Default browser agent now loads the intended NorthCUA Web system template; explicit custom prompts remain unchanged")
