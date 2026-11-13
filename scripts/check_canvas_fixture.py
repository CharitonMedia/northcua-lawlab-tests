#!/usr/bin/env python3
"""Scripted fixture control only. This is not a model evaluation."""
import json,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={"width":1280,"height":720})
 page.goto("http://127.0.0.1:18878/vision/fixture-control")
 box=page.locator("canvas").bounding_box()
 for x in (300,700):
  page.mouse.click(box["x"]+x,box["y"]+330);page.wait_for_timeout(150)
 d=json.load(urllib.request.urlopen("http://127.0.0.1:18878/api/state/fixture-control"))
 assert d["data"]["sequence"]==["teal-hexagon","purple-circle"]
 Path("results/environment/canvas-fixture-control.json").write_text(json.dumps({"type":"scripted fixture validation; not a model task result","canvas_bounds":box,"receipt":d},indent=2))
 browser.close()
 print("Canvas event handling and persistent receipt PASS")
