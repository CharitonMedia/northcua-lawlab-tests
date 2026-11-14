#!/usr/bin/env python3
"""End-to-end scripted controls. Never count these as real-model capability runs."""
import json,os,subprocess,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/"results/hardening/controls";folder.mkdir(parents=True,exist_ok=True)
cfgroot=ROOT/"config/controls";cfgroot.mkdir(parents=True,exist_ok=True)
base=ROOT/"config/nano-q8-hardened"
rows=[]
for mode,task in [("always-finish","project"),("loop","settings"),("date-recovery","project"),("date-budget","project")]:
 cfg=cfgroot/mode;cfg.mkdir(parents=True,exist_ok=True)
 app=yaml.safe_load((base/"app.example.yaml").read_text())
 app["artifacts"]["root_dir"]="results/hardening/controls/harness"
 if mode!="always-finish":app["web"]["completion_evidence_selector"]=None
 (cfg/"app.yaml").write_text(yaml.safe_dump(app,sort_keys=False))
 for name in ("agent.example.yaml","agent.web.example.yaml"):
  agent=yaml.safe_load((base/name).read_text());agent["llm_config"]["model"]="scripted-integration-control";agent["llm_config"]["base_url"]=f"http://127.0.0.1:19096/{mode}/v1";(cfg/name).write_text(yaml.safe_dump(agent,sort_keys=False))
 run="control-"+mode
 env=dict(os.environ,OPENAI_API_KEY="local-no-auth",PYTHONPATH=str(ROOT/"scripts/recording"),NORTHCUA_VIDEO_DIR=str(folder/mode/"video"))
 cmd=[str(ROOT/"vendor/NorthCUA/.venv/bin/northcua"),"local","web","run","--app-config",str(cfg/"app.yaml"),"--url",f"http://127.0.0.1:18878/{task}/{run}","--query","Controlled integration check. Fill the date if requested, otherwise inspect the page.","--max-steps","20","--session-id",run,"--no-evaluate"]
 with(folder/(mode+"-console.log")).open("w")as f:rc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
 result=json.loads((folder/"harness"/run/"result.json").read_text())
 requests=[json.loads(l)for l in(folder/(mode+"-requests.jsonl")).read_text().splitlines()]
 tools=[t for s in result["steps"]for t in s.get("tools",[])]
 feedback=any(r["runtime_feedback_present"]for r in requests)
 if mode=="always-finish":passed=result["terminal_status"]=="verification_failed"and feedback and not result["success"]
 elif mode=="loop":passed=feedback and len(result["steps"])<20
 elif mode=="date-recovery":passed=any(t.get("tool_output",{}).get("code")=="invalid_date_format"and t.get("tool_output",{}).get("retryable")is True for t in tools)and any(t.get("tool_input",{}).get("text")=="2026-12-01"and not t.get("is_error")for t in tools)
 else:passed=result["terminal_status"]=="tool_error"and len(result["steps"])==4 and not result["success"]
 rows.append({"control":mode,"kind":"scripted integration control, not a real-model task","passed":passed,"exit_code":rc,"status":result["status"],"terminal_status":result["terminal_status"],"steps":len(result["steps"]),"runtime_feedback_delivered":feedback})
 print(json.dumps(rows[-1]),flush=True)
(folder/"summary.json").write_text(json.dumps(rows,indent=2))
if not all(r["passed"]for r in rows):raise SystemExit(1)
