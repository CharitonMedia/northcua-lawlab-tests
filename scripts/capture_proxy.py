#!/usr/bin/env python3
"""Record model calls and timings. Image data becomes hashed separate files."""
import json,time,urllib.request,urllib.error,hashlib,base64,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(os.getenv("CAPTURE_ROOT","results"));ROOT.mkdir(exist_ok=True,parents=True)
def clean(x):
 if isinstance(x,dict):return{k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return[clean(v) for v in x]
 if isinstance(x,str) and x.startswith("data:image/") and ";base64," in x:
  head,b=x.split(",",1);raw=base64.b64decode(b);h=hashlib.sha256(raw).hexdigest();p=ROOT/"images";p.mkdir(exist_ok=True);ext="png" if "png" in head else "jpg";name=f"{h}.{ext}";(p/name).write_bytes(raw);return f"image:images/{name} sha256:{h}"
 return x
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  req=json.loads(self.rfile.read(int(self.headers["Content-Length"])));req["stream"]=False;start=time.time();status=200
  try:
   r=urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:19093"+self.path,data=json.dumps(req).encode(),headers={"Content-Type":"application/json"}),timeout=240);body=r.read()
  except urllib.error.HTTPError as e:status=e.code;body=e.read()
  except Exception as e:status=502;body=json.dumps({"error":str(e)}).encode()
  run=Path(".runtime/current-run").read_text().strip() if Path(".runtime/current-run").exists() else "smoke"
  entry={"run_id":run,"started_at_unix":start,"elapsed_seconds":time.time()-start,"http_status":status,"request":clean(req),"response":clean(json.loads(body))}
  with(ROOT/"model-calls.jsonl").open("a") as f:f.write(json.dumps(entry)+"\n")
  self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",19094),Handler).serve_forever()
