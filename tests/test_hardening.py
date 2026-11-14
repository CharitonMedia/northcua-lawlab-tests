import unittest
from playwright.async_api import async_playwright
from northcua.core.config import WebAgentConfig
from northcua.agents.web.backend.playwright import PlaywrightWebActionBackend
from northcua.agents.web.backend.errors import WebActionCommandError
from northcua.agents.web.domain.actions import WebMouseButton
from northcua.agents.web.hardening import map_point,repeated_cycle
from northcua.agents.web.mcp.error_classification import classify_web_tool_error

class PolicyTests(unittest.TestCase):
 def test_normalized_sizes_and_edges(self):
  self.assertEqual(map_point(346,658,width=1280,height=720,input_space="normalized_1000",clamp=True),(443,474))
  self.assertEqual(map_point(500,500,width=1440,height=900,input_space="normalized_1000",clamp=True),(720,450))
  self.assertEqual(map_point(1000,1000,width=1440,height=900,input_space="normalized_1000",clamp=True),(1439,899))
 def test_pixels_not_scaled_and_invalid_values_rejected(self):
  self.assertEqual(map_point(346,658,width=1280,height=720,input_space="viewport_css",clamp=False),(346,658))
  for x in [float("nan"),float("inf"),-1,1001]:
   with self.assertRaises(ValueError):map_point(x,100,width=1280,height=720,input_space="normalized_1000",clamp=False)
 def test_cycle_requires_repeated_action_and_state(self):
  self.assertTrue(repeated_cycle(["a","b"]*3))
  self.assertTrue(repeated_cycle(["a"]*3))
  self.assertFalse(repeated_cycle(["a","b","a","b","a","new-state"]))
  self.assertFalse(repeated_cycle(["a","b"]*2))

class BrowserTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.backend=PlaywrightWebActionBackend(config=WebAgentConfig(coordinate_policy={"input_space":"normalized_1000","clamp_to_bounds":True}),session_id="regression")
  self.page=await self.backend._page()
 async def asyncTearDown(self):await self.backend.close()
 async def test_point_click_tracks_live_resize(self):
  await self.page.set_content("<script>window.points=[];document.addEventListener('click',e=>points.push([e.clientX,e.clientY]));</script>")
  for w,h in [(1280,720),(1440,900)]:
   await self.page.set_viewport_size({"width":w,"height":h})
   result=await self.backend._click_point(500,500,WebMouseButton.LEFT,click_count=1)
   self.assertEqual((result["x"],result["y"]),(w//2,h//2))
  self.assertEqual(await self.page.evaluate("points"),[[640,360],[720,450]])
 async def test_drag_maps_both_endpoints_once(self):
  await self.page.set_content("<script>window.points=[];document.addEventListener('mousedown',e=>points.push([e.clientX,e.clientY]));document.addEventListener('mouseup',e=>points.push([e.clientX,e.clientY]));</script>")
  await self.page.set_viewport_size({"width":1440,"height":900})
  result=await self.backend._drag_point(250,250,750,750)
  self.assertEqual(result["from"],{"x":360,"y":225})
  self.assertEqual(result["to"],{"x":1080,"y":675})
  self.assertEqual(await self.page.evaluate("points"),[[360,225],[1080,675]])
 async def test_date_error_is_correctable_and_does_not_mutate(self):
  await self.page.set_content('<label>Start date<input type="date" id="d"></label>')
  snap=await self.backend.snapshot();ref=next(e for e in snap.elements if e.tag=="input").model_ref
  with self.assertRaises(WebActionCommandError) as caught:await self.backend._fill_ref(ref,"12/01/2026")
  error=classify_web_tool_error(caught.exception)
  self.assertEqual(error.code,"invalid_date_format");self.assertTrue(error.retryable)
  self.assertIn("YYYY-MM-DD",error.hint)
  self.assertEqual(await self.page.locator("#d").input_value(),"")
  await self.backend._fill_ref(ref,"2026-12-01")
  self.assertEqual(await self.page.locator("#d").input_value(),"2026-12-01")
 async def test_evidence_requires_nonempty_rendered_marker(self):
  await self.page.set_content('<p role="status"></p><p role="status" hidden>fake hidden receipt</p>')
  self.assertFalse((await self.backend.completion_evidence('[role="status"]'))["ok"])
  # Explicitly await the script result before checking.
  await self.page.evaluate("document.querySelector('[role=status]').textContent='Saved receipt 42'")
  result=await self.backend.completion_evidence('[role="status"]')
  self.assertEqual(result["visible_evidence"],["Saved receipt 42"])
if __name__=="__main__":unittest.main()
