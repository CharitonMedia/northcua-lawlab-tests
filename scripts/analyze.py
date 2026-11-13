#!/usr/bin/env python3
"""Derive public summaries without conflating completion and saved-state checks."""
import json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RESULTS=ROOT/"results"
calls=[json.loads(l) for l in (RESULTS/"model-calls.jsonl").read_text().splitlines()]
rows=[]
for p in sorted((RESULTS/"runs").glob("*/outcome.json")):
 d=json.loads(p.read_text());h=json.loads((RESULTS/"harness"/d["run_id"]/"result.json").read_text());c=[x for x in calls if x["run_id"]==d["run_id"]]
 t=[x["response"].get("timings",{}) for x in c]
 predicted=sum(x.get("predicted_n",0)for x in t);ms=sum(x.get("predicted_ms",0)for x in t)
 rows.append({"run_id":d["run_id"],"case_id":d["case_id"],"started_at_unix":d["started_at_unix"],"wall_seconds":d["wall_seconds"],"harness_status":h["status"],"terminal_status":h["terminal_status"],"steps":len(h["steps"]),"saved_state_pass":d["independent_saved_state_pass"],"end_to_end_pass":d["independent_saved_state_pass"] and h["status"]=="success" and h["terminal_status"]=="completed" and d["exit_code"]==0,"exit_code":d["exit_code"],"model_calls":len(c),"completion_tokens":predicted,"model_decode_seconds":ms/1000,"decode_tokens_per_second":predicted/(ms/1000)if ms else None,"overlapping_runs":[]})
for a in rows:
 for b in rows:
  if a is not b and max(a["started_at_unix"],b["started_at_unix"])<min(a["started_at_unix"]+a["wall_seconds"],b["started_at_unix"]+b["wall_seconds"]):a["overlapping_runs"].append(b["run_id"])
baseline=[x for x in rows if x["run_id"].startswith("baseline-")]
summary={"total_model_task_runs":len(rows),"baseline_runs":len(baseline),"baseline_end_to_end_pass":sum(x["end_to_end_pass"]for x in baseline),"baseline_saved_state_pass":sum(x["saved_state_pass"]for x in baseline),"rows":rows,"timing_note":"Overlapping runs are retained but excluded from single-request latency interpretation. Decode rates come from llama.cpp predicted_n/predicted_ms and exclude prefill, vision and orchestration."}
(RESULTS/"summary.json").write_text(json.dumps(summary,indent=2))
with(RESULTS/"summary.csv").open("w")as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(json.dumps(summary,indent=2))
