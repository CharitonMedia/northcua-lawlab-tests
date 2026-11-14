#!/usr/bin/env python3
"""Historical V1 generator. Use the published final patch for reproduction."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "vendor/NorthCUA"


def edit(name, old, new):
    p = V / name
    s = p.read_text()
    if old not in s:
        raise RuntimeError("Patch anchor missing: " + name + " " + old[:70])
    p.write_text(s.replace(old, new, 1))


config = "northcua/core/config.py"
edit(
    config,
    "class WebAgentConfig(BaseModel):",
    '''class WebPointCoordinatePolicyConfig(BaseModel):
    """Model-facing Web point policy. Ref actions are never scaled."""
    model_config = ConfigDict(extra="forbid")
    input_space: Literal["viewport_css", "normalized_1000"] = "viewport_css"
    clamp_to_bounds: bool = False


class WebAgentConfig(BaseModel):''',
)
edit(
    config,
    '    playwright_browser: Literal["chromium", "firefox", "webkit"] = "chromium"',
    '''    coordinate_policy: WebPointCoordinatePolicyConfig = Field(default_factory=WebPointCoordinatePolicyConfig)
    viewport_width: int = Field(default=1280, ge=320)
    viewport_height: int = Field(default=720, ge=240)
    recovery_error_budget: int | None = Field(default=None, ge=0)
    loop_detection_enabled: bool = False
    completion_evidence_selector: str | None = None
    completion_recovery_budget: int = Field(default=2, ge=0)
    playwright_browser: Literal["chromium", "firefox", "webkit"] = "chromium"''',
)
helper = V / "northcua/agents/web/hardening.py"
helper.write_text('''"""Coordinate contract and repeated-cycle checks without task-specific answers."""
from __future__ import annotations
import math

def map_point(x: float, y: float, *, width: int, height: int, input_space: str, clamp: bool) -> tuple[float, float]:
    if not all(math.isfinite(v) for v in (x,y)) or width <= 0 or height <= 0:
        raise ValueError("Non-finite point or invalid viewport")
    if input_space == "normalized_1000":
        x, y = round(x * width / 1000), round(y * height / 1000)
    elif input_space != "viewport_css":
        raise ValueError("Unknown Web point coordinate space")
    if clamp:
        x,y=max(0,min(width-1,x)),max(0,min(height-1,y))
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError("point outside viewport")
    return x,y

def repeated_cycle(history: list[str], *, repeats: int = 3) -> bool:
    """Require repeated identical action+pre-observation cycles; not just repeated tools."""
    for period in (1,2,3):
        if len(history)>=period*repeats:
            window=history[-period*repeats:]
            if all(window[i:i+period]==window[:period] for i in range(0,len(window),period)):
                return True
    return False
''')
back = "northcua/agents/web/backend/playwright.py"
edit(back, "import re\n", "import re\nfrom datetime import date\n\nfrom ..hardening import map_point\n")
edit(
    back,
    "        return WebSnapshotObservation(\n",
    """        viewport = page.viewport_size or _DEFAULT_VIEWPORT
        space = self.config.coordinate_policy.input_space
        snapshots.append(f"[Runtime point coordinate policy: {space}; current viewport {viewport['width']}x{viewport['height']}. Ref actions do not use coordinates.]")
        date_refs = [e.ref_id for e in elements if e.attributes.get("type") == "date"]
        if date_refs:
            snapshots.append("[HTML date inputs " + ", ".join(date_refs) + " require YYYY-MM-DD values.]")
        return WebSnapshotObservation(
""",
)
edit(
    back,
    '                "backend": "playwright",',
    """                "backend": "playwright",
                "point_coordinate_input_space": space,
                "viewport": viewport,""",
)
edit(
    back,
    "        await locator.fill(text, timeout=self.config.command_timeout_seconds * 1000)",
    """        if await locator.get_attribute("type") == "date" and text:
            try:
                if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", text):
                    raise ValueError("Expected YYYY-MM-DD")
                date.fromisoformat(text)
            except ValueError as exc:
                raise WebActionCommandError(
                    "Invalid HTML date value; use YYYY-MM-DD.",
                    code="invalid_date_format",
                    hint="Correct the date to YYYY-MM-DD using the requested date, then retry this field. Do not guess a different date.",
                ) from exc
        await locator.fill(text, timeout=self.config.command_timeout_seconds * 1000)""",
)
edit(
    back,
    '            await self._validate_point(x, y)\n            page = await self._page()\n            await page.mouse.click(x, y, button=button.value, click_count=click_count)\n            return {"x": x, "y": y, "button": button.value, "click_count": click_count}',
    """            page = await self._page()
            mapped_x, mapped_y = await self._map_point(x, y)
            await page.mouse.click(mapped_x, mapped_y, button=button.value, click_count=click_count)
            return {"x": mapped_x, "y": mapped_y, "model_point": {"x":x, "y":y},
                    "input_space": self.config.coordinate_policy.input_space,
                    "button": button.value, "click_count": click_count}""",
)
edit(
    back,
    """        await self._validate_point(from_x, from_y)
        await self._validate_point(to_x, to_y)""",
    """        from_x, from_y = await self._map_point(from_x, from_y)
        to_x, to_y = await self._map_point(to_x, to_y)""",
)
edit(
    back,
    "    async def _validate_point(self, x: float, y: float) -> None:",
    '''    async def _map_point(self, x: float, y: float) -> tuple[float,float]:
        page = await self._page()
        viewport = page.viewport_size or await page.evaluate("({width:innerWidth,height:innerHeight})")
        return map_point(x,y,width=viewport["width"],height=viewport["height"],
                         input_space=self.config.coordinate_policy.input_space,
                         clamp=self.config.coordinate_policy.clamp_to_bounds)

    async def completion_evidence(self, selector: str) -> dict[str,object]:
        """Read visible evidence only; never infer task values or mutate the page."""
        page=await self._page()
        targets=page.locator(selector)
        evidence=[]
        for i in range(await targets.count()):
            node=targets.nth(i)
            if await node.is_visible():
                text=(await node.inner_text()).strip()
                if text:evidence.append(text[:4000])
        return {"ok":bool(evidence), "visible_evidence":evidence, "selector":selector}

    async def _validate_point(self, x: float, y: float) -> None:''',
)
edit(
    back,
    "self._browser.new_context(viewport=_DEFAULT_VIEWPORT)",
    'self._browser.new_context(viewport={"width":self.config.viewport_width,"height":self.config.viewport_height})',
)
# Keep point overlays in the same frame as executed points, including HiDPI screenshots.
overlay = "northcua/agents/web/overlay/action_adapter.py"
edit(overlay, "from ..domain.actions import", "from ..hardening import map_point\nfrom ..domain.actions import")
edit(
    overlay,
    "        payload = dict(params or {})\n",
    """        payload = dict(params or {})
        if observation.snapshot.raw.get("point_coordinate_input_space") == "normalized_1000":
            viewport = observation.snapshot.raw.get("viewport")
            if isinstance(viewport, Mapping) and action in {
                WebAgentActionType.CLICK_POINT, WebAgentActionType.DOUBLE_CLICK_POINT, WebAgentActionType.DRAG_POINT
            }:
                pairs = [("from_x","from_y"),("to_x","to_y")] if action == WebAgentActionType.DRAG_POINT else [("x","y")]
                for xkey,ykey in pairs:
                    payload[xkey],payload[ykey]=map_point(float(payload[xkey]),float(payload[ykey]),
                        width=int(viewport["width"]),height=int(viewport["height"]),
                        input_space="normalized_1000",clamp=True)
""",
)
actions = "northcua/agents/web/domain/actions.py"
edit(
    actions,
    '"use this instead of a click/type sequence when a reliable input ref exists. Use web_type_text only "',
    '"HTML date inputs require YYYY-MM-DD (ISO) values. Use this instead of a click/type sequence when a reliable input ref exists. Use web_type_text only "',
)
# Model-facing point descriptions must agree with runtime policy.
for name in [
    actions,
    "northcua/agents/web/mcp/descriptors.py",
    "northcua/agents/web/prompt/templates/web_agent_system.j2",
]:
    p = V / name
    s = p.read_text()
    s = s.replace(
        "Current viewport CSS x coordinate from the viewport's top-left corner.",
        "Viewport x coordinate in the input space declared by the latest runtime observation.",
    )
    s = s.replace(
        "Current viewport CSS y coordinate from the viewport's top-left corner.",
        "Viewport y coordinate in the input space declared by the latest runtime observation.",
    )
    s = s.replace(
        "Click current viewport CSS coordinates only",
        "Click coordinates in the input space declared by the latest runtime observation only",
    )
    s = s.replace(
        "Double-click current viewport CSS coordinates only",
        "Double-click coordinates in the input space declared by the latest runtime observation only",
    )
    s = s.replace(
        "Drag from one current viewport CSS coordinate to another",
        "Drag between coordinates in the input space declared by the latest runtime observation",
    )
    s = s.replace(
        "- Point coordinates are CSS pixels relative to the current viewport top-left: x increases to the right and y increases downward.",
        "- Use the point-coordinate policy in the latest observation. normalized_1000 means x and y range from 0 to 1000 across the viewport; emit these directly and let the backend convert once. viewport_css means CSS pixels. Ref actions never need scaling.",
    )
    p.write_text(s)
p = V / "northcua/agents/web/prompt/templates/web_agent_system.j2"
p.write_text(
    p.read_text()
    + """
Reliable form input and stopping:
- For HTML date inputs, supply YYYY-MM-DD values even when the control visually uses a local date format.
- Verify every requested value once after saving/reopening. Keep a checklist of which values are already verified.
- When all values have been verified and the page shows the saved result, finish immediately. Do not alternate tabs to recheck values already confirmed.
- Never claim a saved result or recorded click sequence unless it appears in the latest visible page evidence. A successful click tool alone does not prove a target was hit.
"""
)
loop = "northcua/agents/web/runner/run_loop.py"
edit(loop, "import logging\n", "import logging\nimport json\nimport hashlib\n")
edit(
    loop,
    "from ..backend import WebActionBackend\n",
    "from ..backend import WebActionBackend\nfrom ..hardening import repeated_cycle\n",
)
edit(
    loop,
    "    recent_action_result: JsonObject | None = None\n",
    """    runtime_feedback: str = ""
    recoverable_error_steps: int = 0
    completion_rejections: int = 0
    cycle_history: list[str] = field(default_factory=list)
    loop_warnings: int = 0
    recent_action_result: JsonObject | None = None
""",
)
edit(
    loop,
    "            user_query=self.spec.user_query,\n",
    '            user_query=self.spec.user_query + ("\\nRuntime feedback: " + self.runtime_feedback if self.runtime_feedback else ""),\n',
)
edit(
    loop,
    """            if final_answer:
                return self._finish_final_answer(context, step_record, final_answer)""",
    """            if final_answer:
                selector=self.runner.app_config.web.completion_evidence_selector
                infeasible = TerminalDecisionPolicy().failure_reason_from_text(final_answer) == AgentTerminalReason.INFEASIBLE
                if selector and not infeasible:
                    evidence = await client.completion_evidence(selector)
                    with (Path(self.runner.artifact_store.root)/"completion_checks.jsonl").open("a") as stream:
                        stream.write(json.dumps({"step":step_index,**evidence})+"\\n")
                    if not evidence["ok"]:
                        self.completion_rejections += 1
                        if self.completion_rejections > self.runner.app_config.web.completion_recovery_budget:
                            return self._stop_with_reason(context,step_record,WebTerminalStatus.VERIFICATION_FAILED,
                                "No visible completion evidence after bounded recovery.")
                        self.runtime_feedback = ("Your completion claim has no visible confirmation or receipt on the page. "
                            "Inspect the latest observation and correct any missing action. Do not invent confirmation. "
                            "If blocked, report the blocker rather than claiming success.")
                        self.prior_messages = self.runner.prompt_builder.append_step_history(
                            envelope=step_result.envelope,prior_messages=self.prior_messages,trace_state=step_result.trace_state)
                        self.current_observation=None
                        self.recent_post_action_observation=None
                        return AgentRuntimeStepOutcome(cursor=context.cursor,result=step_record,
                            terminal_decision=self.result.to_terminal_decision(),summary="Completion evidence missing; bounded recovery.")
                return self._finish_final_answer(context, step_record, final_answer)""",
)
edit(
    loop,
    """        if errored_action is not None:
            return self._finish_tool_error(context, step_record, step_result, errored_action)
        return AgentRuntimeStepOutcome(""",
    """        if errored_action is not None:
            return self._finish_tool_error(context, step_record, step_result, errored_action)
        retryable = next((action for action in resolved_actions if action.is_error and action.is_retryable_error),None)
        if retryable is not None:
            self.recoverable_error_steps += 1
            budget=self.runner.app_config.web.recovery_error_budget
            if budget is not None and self.recoverable_error_steps > budget:
                return self._stop_with_reason(context,step_record,WebTerminalStatus.TOOL_ERROR,
                    "Correctable tool-error recovery budget exhausted.")
        if self.runner.app_config.web.loop_detection_enabled:
            signature=json.dumps([(a.tool_name,a.tool_input) for a in resolved_actions],sort_keys=True)+observation.snapshot.snapshot
            self.cycle_history.append(hashlib.sha256(signature.encode()).hexdigest())
            if repeated_cycle(self.cycle_history):
                self.loop_warnings += 1
                self.cycle_history.clear()
                if self.loop_warnings > 1:
                    return self._stop_with_reason(context,step_record,WebTerminalStatus.NO_PROGRESS,
                        "Repeated action/observation cycle continued after a recovery warning.")
                self.runtime_feedback = ("You repeated the same actions through the same page states without new progress. "
                    "Review the saved confirmation and requested values once. Finish if verified; otherwise take one "
                    "specific corrective action. Stop alternating tabs or repeating already completed checks.")
        return AgentRuntimeStepOutcome(""",
)
edit(
    loop,
    "    def _finish_final_answer(\n",
    """    def _stop_with_reason(self,context,step_record,reason,detail):
        self.result.success=False
        self.result.status=WebRunStatus.FAILED
        self.result.terminal_status=reason
        self.result.final_answer=detail
        return AgentRuntimeStepOutcome(cursor=context.cursor,result=step_record,
            terminal_decision=self.result.to_terminal_decision(),summary=detail)

    def _finish_final_answer(
""",
)
edit(
    "northcua/agents/web/domain/results.py",
    '    RUNTIME_ERROR = "runtime_error"\n',
    '    RUNTIME_ERROR = "runtime_error"\n    NO_PROGRESS = "no_progress"\n    VERIFICATION_FAILED = "verification_failed"\n',
)
print("Applied opt-in Web coordinate, date, recovery and completion-evidence patch")
