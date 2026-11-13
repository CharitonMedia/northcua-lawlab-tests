#!/usr/bin/env python3
"""Synthetic browser fixtures. Server-side receipts enable independent checks."""
import json,time,os
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(os.getenv("FIXTURE_DATA","results/fixture-state"));ROOT.mkdir(parents=True,exist_ok=True)
PAGES={
"project":'''<h1>Project planner</h1><a href="">Reopen saved project</a><form id="form">
<label>Project name<input name="name" required></label>
<label>Category<select name="category"><option>Research</option><option>Design</option><option>Operations</option></select></label>
<label>Priority<select name="priority"><option>Low</option><option>Normal</option><option>High</option></select></label>
<label>Start date<input type="date" name="start" required></label>
<label>Budget<input type="number" name="budget" step="0.01" required></label>
<label>Notes<textarea name="notes"></textarea></label>
<label><input type="checkbox" name="notifications">Enable notifications</label>
<button>Save project</button></form>''',
"shop":'''<h1>Supply shop</h1><label>Category filter<select id="filter"><option>All</option><option>Lamp</option><option>Chair</option></select></label>
<label><input type="checkbox" id="stock">In stock only</label><label>Sort<select id="sort"><option value="sku">SKU</option><option value="price">Price ascending</option></select></label>
<form id="form"><table><thead><tr><th>Select</th><th>SKU</th><th>Product</th><th>Category</th><th>Price</th><th>Stock</th></tr></thead><tbody id="items"></tbody></table>
<label>Quantity<input name="quantity" type="number" min="1" value="1"></label><label>Delivery<select name="delivery"><option>Standard</option><option>Express</option></select></label>
<button>Place test order</button></form><script>
const products=[{sku:"L11",name:"Pocket lamp",category:"Lamp",price:9.95,stock:false},{sku:"L17",name:"Desk lamp",category:"Lamp",price:24.5,stock:true},{sku:"L42",name:"Studio lamp",category:"Lamp",price:32,stock:true},{sku:"C12",name:"Folding chair",category:"Chair",price:18,stock:true}];
function render(){let a=products.filter(p=>(filter.value==="All"||p.category===filter.value)&&(!stock.checked||p.stock));a.sort((a,b)=>sort.value==="price"?a.price-b.price:a.sku.localeCompare(b.sku));
items.innerHTML=a.map(p=>'<tr><td><input type="radio" name="sku" value="'+p.sku+'" required '+(!p.stock?'disabled':'')+' aria-label="Select '+p.name+'"></td><td>'+p.sku+'</td><td>'+p.name+'</td><td>'+p.category+'</td><td>$'+p.price.toFixed(2)+'</td><td>'+(p.stock?'In stock':'Unavailable')+'</td></tr>').join("");}
for(const id of ["filter","stock","sort"])document.getElementById(id).onchange=render;render();</script>''',
"settings":'''<h1>Workspace settings</h1><nav><button type="button" onclick="tab('display')">Display</button><button type="button" onclick="tab('alerts')">Notifications</button><a href="">Reload saved settings</a></nav>
<form id="form"><section id="display"><h2>Display</h2><label>Theme<select name="theme"><option>Light</option><option>Dark</option></select></label>
<label>Language<select name="language"><option>English</option><option>Spanish</option><option>French</option></select></label>
<label>Date format<select name="date_format"><option>MM/DD/YYYY</option><option>YYYY-MM-DD</option></select></label>
<label>Time zone<select name="timezone"><option>America/New_York</option><option>UTC</option><option>Europe/London</option></select></label></section>
<section id="alerts" hidden><h2>Notifications</h2><label><input type="checkbox" name="newsletter" checked>Weekly newsletter</label><label><input type="checkbox" name="autosave">Autosave reminders</label></section><button>Save settings</button></form>
<script>function tab(id){for(const s of document.querySelectorAll("section"))s.hidden=s.id!==id;}</script>'''
}

PAGES["vision"]='<h1>Visual target board</h1><p>Click the requested shapes. The shapes are drawn on a canvas.</p><canvas id="board" width="1000" height="470" style="background:white;border:1px solid #aaa"></canvas><p id="status"></p><script>\nconst c=document.getElementById("board"),ctx=c.getContext("2d");let seq=[],clicks=[];\nconst shapes=[{id:"blue-circle",x:150,y:110,color:"#2463c7",kind:"circle",label:"BLUE CIRCLE"},{id:"orange-triangle",x:500,y:110,color:"#d77815",kind:"triangle",label:"ORANGE TRIANGLE"},{id:"red-square",x:830,y:110,color:"#c53030",kind:"square",label:"RED SQUARE"},{id:"teal-hexagon",x:300,y:330,color:"#087e83",kind:"hexagon",label:"TEAL HEXAGON"},{id:"purple-circle",x:700,y:330,color:"#8035a6",kind:"circle",label:"PURPLE CIRCLE"}];\nfunction draw(){ctx.clearRect(0,0,1000,470);for(const s of shapes){ctx.fillStyle=s.color;ctx.beginPath();if(s.kind==="circle")ctx.arc(s.x,s.y,52,0,2*Math.PI);else if(s.kind==="square")ctx.rect(s.x-50,s.y-50,100,100);else{let n=s.kind==="triangle"?3:6;for(let i=0;i<n;i++){let a=-Math.PI/2+2*Math.PI*i/n;let x=s.x+58*Math.cos(a),y=s.y+58*Math.sin(a);i?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.closePath();}ctx.fill();ctx.fillStyle="#17233a";ctx.font="18px system-ui";ctx.textAlign="center";ctx.fillText(s.label,s.x,s.y+85);}}\ndraw();c.onclick=async e=>{const r=c.getBoundingClientRect(),x=(e.clientX-r.left)*1000/r.width,y=(e.clientY-r.top)*470/r.height;const hit=shapes.find(s=>Math.hypot(s.x-x,s.y-y)<60);seq.push(hit?hit.id:"miss");clicks.push({x,y,viewport_x:e.clientX,viewport_y:e.clientY});await fetch("/api/save/"+location.pathname.split("/").pop(),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task:"vision",data:{sequence:seq,click_count:clicks.length,clicks}})});document.getElementById("status").textContent="Recorded clicks: "+seq.join(", ");};</script>'
STYLE="""body{font:18px system-ui;margin:30px auto;max-width:1000px;background:#f5f7fb;color:#17233a}h1{color:#164b76}label{display:block;margin:14px 0}input,select,textarea,button{font:inherit;padding:8px;margin-left:12px}input[type=checkbox],input[type=radio]{margin:0 8px}button{background:#164b76;color:white;border:0;border-radius:5px;cursor:pointer}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border-bottom:1px solid #ccc}nav{margin-bottom:20px}a{margin:15px}#receipt{font-weight:bold;color:#175d31}"""
SCRIPT=r"""
const run=location.pathname.split("/").pop(),task=location.pathname.split("/")[1];
function values(){const f=document.querySelector("#form");let d=Object.fromEntries(new FormData(f));for(const e of f.querySelectorAll('input[type=checkbox]'))d[e.name]=e.checked;return d;}
async function saved(){const s=await(await fetch("/api/state/"+run)).json();if(s.data){for(const[k,v]of Object.entries(s.data)){const e=document.querySelector('[name="'+k+'"]');if(!e)continue;if(e.type==="checkbox")e.checked=v;else if(e.type!=="radio")e.value=v;}document.querySelector("#receipt").textContent="Saved "+task+": "+JSON.stringify(s.data);}}
document.querySelector("#form").onsubmit=async e=>{e.preventDefault();const r=await fetch("/api/save/"+run,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({task,data:values()})});const s=await r.json();document.querySelector("#receipt").textContent="Saved "+task+": "+JSON.stringify(s.data);};saved();
"""
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=self.path.split("?")[0]
  if path.startswith("/api/state/"):
   p=ROOT/(path.rsplit("/",1)[-1]+".json");return self.send(200,p.read_bytes() if p.exists() else b"{}","application/json")
  kind=path.strip("/").split("/")[0]
  if kind not in PAGES:return self.send(404,b"Not found","text/plain")
  html='<!doctype html><html><head><meta charset="utf-8"><title>NorthCUA '+kind+' test</title><style>'+STYLE+'</style></head><body>'+PAGES[kind]+'<p id="receipt" role="status"></p><script>'+(SCRIPT if kind!="vision" else "")+'</script></body></html>'
  self.send(200,html.encode(),"text/html")
 def do_POST(self):
  run=self.path.rsplit("/",1)[-1]
  if not self.path.startswith("/api/save/") or not run.replace("-","").isalnum():return self.send(400,b"{}","application/json")
  d=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
  if d["task"]=="shop":
   x=d["data"];x["total"]=round({"L11":9.95,"L17":24.5,"L42":32,"C12":18}.get(x.get("sku"),0)*int(x.get("quantity",1))+(7.5 if x.get("delivery")=="Express" else 0),2)
  d["saved_at_unix"]=time.time();(ROOT/(run+".json")).write_text(json.dumps(d,indent=2));self.send(200,json.dumps(d).encode(),"application/json")
 def send(self,status,data,mime):
  self.send_response(status);self.send_header("Content-Type",mime);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",18878),Handler).serve_forever()
