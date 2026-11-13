#!/usr/bin/env python3
"""Bounded real-model runs with independent fixture-state checks and video."""
import os,json,time,subprocess,argparse,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=[
{"id":"vision-a","task":"vision","prompt":"Click the TEAL HEXAGON first, then the PURPLE CIRCLE on the visual target board. Use normal browser pointing actions. Stop after those two clicks and report the recorded sequence.","expected":{"sequence":["teal-hexagon","purple-circle"],"click_count":2}},
{"id":"project-a","task":"project","prompt":"Create a project named Ember, category Design, priority High, start date December 1, 2026, budget 1250, notes 'Prototype review'. Enable notifications. Save it, reopen the saved project, and verify every requested value. Use only the normal visible browser controls.","expected":{"name":"Ember","category":"Design","priority":"High","start":"2026-12-01","budget":"1250","notes":"Prototype review","notifications":True}},
{"id":"shop-a","task":"shop","prompt":"Find the least expensive in-stock lamp. Order 3 of it with Express delivery using the normal visible browser controls. Submit the test order and report its SKU and final total. Do not buy an unavailable item.","expected":{"sku":"L17","quantity":"3","delivery":"Express","total":81.0}},
{"id":"settings-a","task":"settings","prompt":"Using the visible workspace settings controls, set theme Dark, language French, date format YYYY-MM-DD, and time zone UTC. On the Notifications tab turn OFF the weekly newsletter and turn ON autosave reminders. Save, reload the saved settings, and verify them.","expected":{"theme":"Dark","language":"French","date_format":"YYYY-MM-DD","timezone":"UTC","newsletter":False,"autosave":True}},
{"id":"project-b","task":"project","prompt":"Create project Atlas, category Operations, priority Normal, start date January 15, 2027, budget 875.50, notes 'Check supply list'. Leave notifications OFF. Save, reopen the saved project, and verify all values. Use only normal visible browser controls.","expected":{"name":"Atlas","category":"Operations","priority":"Normal","start":"2027-01-15","budget":"875.50","notes":"Check supply list","notifications":False}},
{"id":"shop-b","task":"shop","prompt":"Select the least expensive lamp that is currently in stock. Order quantity 2 with Standard delivery. Submit the test order using normal visible controls; verify the SKU and final total.","expected":{"sku":"L17","quantity":"2","delivery":"Standard","total":49.0}},
{"id":"settings-b","task":"settings","prompt":"Set workspace theme Dark, language Spanish, date format YYYY-MM-DD and time zone Europe/London. Under Notifications, disable the weekly newsletter and enable autosave reminders. Save and reload the saved settings, then check all six values. Use only visible controls.","expected":{"theme":"Dark","language":"Spanish","date_format":"YYYY-MM-DD","timezone":"Europe/London","newsletter":False,"autosave":True}}
]
def main():
 lock=open(ROOT/".runtime/suite.lock","w")
 fcntl.flock(lock,fcntl.LOCK_EX)
 ap=argparse.ArgumentParser();ap.add_argument("--case");ap.add_argument("--limit",type=int,default=20);ap.add_argument("--tag",default="baseline");ap.add_argument("--iso-date-hint",action="store_true");args=ap.parse_args()
 cases=[c for c in CASES if not args.case or c["id"]==args.case]
 for original in cases:
  case=dict(original)
  if args.iso_date_hint:case["prompt"]+=" When filling an HTML date input, pass its value in YYYY-MM-DD format."
  run=args.tag+"-"+case["id"];out=ROOT/"results"/"runs"/run
  if out.exists():raise RuntimeError("Refusing to overwrite "+str(out))
  out.mkdir(parents=True);(out/"task.json").write_text(json.dumps(case,indent=2))
  (ROOT/".runtime/current-run").write_text(run)
  env=dict(os.environ,OPENAI_API_KEY="local-no-auth",NORTHCUA_VIDEO_DIR=str(out/"video"),PYTHONPATH=str(ROOT/"scripts/recording"))
  cmd=[str(ROOT/"vendor/NorthCUA/.venv/bin/northcua"),"local","web","run","--app-config","config/nano-q8/app.example.yaml","--url","http://127.0.0.1:18878/"+case["task"]+"/"+run,"--query",case["prompt"],"--max-steps",str(args.limit),"--session-id",run,"--no-evaluate"]
  started=time.time();rc=None;timeout=False
  with(out/"console.log").open("w")as f:
   try:rc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600).returncode
   except subprocess.TimeoutExpired:timeout=True
  elapsed=time.time()-started;p=ROOT/"results/fixture-state"/(run+".json")
  saved=json.loads(p.read_text())if p.exists()else{}
  actual=saved.get("data",{});checks={k:(actual.get(k)==v) for k,v in case["expected"].items()}
  # Number inputs may normalize trailing zeros.
  if "budget"in checks:
   try:checks["budget"]=float(actual["budget"])==float(case["expected"]["budget"])
   except(KeyError,ValueError):pass
  result={"run_id":run,"case_id":case["id"],"command":cmd,"started_at_unix":started,"wall_seconds":elapsed,"exit_code":rc,"timed_out":timeout,"expected":case["expected"],"actual":actual,"checks":checks,"independent_saved_state_pass":all(checks.values()),"video_files":[str(v.relative_to(ROOT))for v in out.glob("video/*.webm")]}
  (out/"outcome.json").write_text(json.dumps(result,indent=2))
  print(json.dumps(result),flush=True)
if __name__=="__main__":main()
