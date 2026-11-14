"""Opt-in Playwright video capture without changing upstream harness source."""

import os
from pathlib import Path

if os.getenv("NORTHCUA_VIDEO_DIR"):
    from playwright.async_api import Browser

    original = Browser.new_context

    async def recorded(self, *args, **kwargs):
        p = Path(os.environ["NORTHCUA_VIDEO_DIR"])
        p.mkdir(parents=True, exist_ok=True)
        kwargs.setdefault("record_video_dir", str(p))
        kwargs.setdefault("record_video_size", {"width": 1280, "height": 720})
        return await original(self, *args, **kwargs)

    Browser.new_context = recorded
