#!/usr/bin/env python3
"""Scripted integration controls, not model-capability evaluations."""
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path("results/hardening/controls");ROOT.mkdir(parents=True,exist_ok=True)
COUNTS={}
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  d=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
  mode=self.path.split("/")[1];n=COUNTS.get(mode,0)+1;COUNTS[mode]=n
  text=[]
  for m in d.get("messages",[]):
   c=m.get("content","")
   if isinstance(c,list):c="\n".join(x.get("text","")for x in c if isinstance(x,dict))
   text.append(str(c))
  feedback=any("Runtime feedback:"in t for t in text)
  with(ROOT/(mode+"-requests.jsonl")).open("a")as f:f.write(json.dumps({"call":n,"runtime_feedback_present":feedback,"messages_text":text})+"\n")
  msg={"role":"assistant","content":"The task is complete."}
  call=None
  if mode=="loop" and not feedback:call=("web_click_ref",{"ref":2 if n%2 else 3})
  if mode=="loop" and feedback:msg["content"]="Unable to complete this controlled task; stopping after the runtime warning."
  if mode=="date-recovery" and n<=2:call=("web_fill_ref",{"ref":9,"text":"12/01/2026"if n==1 else"2026-12-01"})
  if mode=="date-recovery" and n>2:msg["content"]="Unable to complete the whole form in this scripted control; date input correction finished."
  if mode=="date-budget":call=("web_fill_ref",{"ref":9,"text":"12/01/2026"})
  if call:
   msg["content"]="Scripted browser control action."
   msg["tool_calls"]=[{"id":f"control-{mode}-{n}","type":"function","function":{"name":call[0],"arguments":json.dumps(call[1])}}]
  body=json.dumps({"id":f"scripted-{mode}-{n}","object":"chat.completion","created":0,"model":"scripted-integration-control","choices":[{"index":0,"message":msg,"finish_reason":"tool_calls"if call else"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1,"total_tokens":2}}).encode()
  self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",19096),Handler).serve_forever()
