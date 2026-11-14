#!/usr/bin/env python3
"""Upgrade the first patch's runtime-feedback delivery; retained as experiment history."""

from pathlib import Path

p = Path(__file__).resolve().parents[1] / "vendor/NorthCUA/northcua/agents/web/runner/run_loop.py"
s = p.read_text()
s = s.replace("from nexau.core.messages import Message\n", "from nexau.core.messages import Message, Role, TextBlock\n")
s = s.replace(
    "        client = self.resource.require_client()\n        observation = await self._current_observation()",
    """        client = self.resource.require_client()
        if self.runtime_feedback:
            self.prior_messages.append(Message(role=Role.USER, content=[
                TextBlock(text="Runtime feedback: " + self.runtime_feedback)
            ]))
            self._record_hardening_event(step_index, "feedback_delivered", self.runtime_feedback)
            self.runtime_feedback = ""
        observation = await self._current_observation()""",
)
s = s.replace(
    'user_query=self.spec.user_query + ("\\nRuntime feedback: " + self.runtime_feedback if self.runtime_feedback else ""),',
    "user_query=self.spec.user_query,",
)
s = s.replace(
    "                self.cycle_history.clear()\n",
    '                self.cycle_history.clear()\n                self._record_hardening_event(step_index,"repeated_cycle",str(self.loop_warnings))\n',
)
s = s.replace(
    "    def _stop_with_reason(self,context,step_record,reason,detail):",
    """    def _record_hardening_event(self,step,kind,detail):
        with (Path(self.runner.artifact_store.root)/"hardening_events.jsonl").open("a") as stream:
            stream.write(json.dumps({"step":step,"kind":kind,"detail":detail})+"\\n")

    def _stop_with_reason(self,context,step_record,reason,detail):""",
)
p.write_text(s)
print("Runtime feedback will be delivered as a retained user message")
