"""Export only public observations and sanitized agent artifacts; never server credentials."""
import json
import shutil
import sys
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT.parent/"virtual-biolab"
sys.path.insert(0,str(LAB))
from virtual_assay.replay import replay_observation

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,separators=(",",":"),allow_nan=False))

headers={"X-Operator-Key":(LAB/"runtime/operator.key").read_text().strip()}
out=ROOT/"dist/data"
with httpx.Client(base_url="http://127.0.0.1:8780",headers=headers,timeout=90) as client:
    def get(path):
        response=client.get(path);response.raise_for_status();return response.json()
    runs=get("/admin/runs");agents=get("/admin/agents");index=[]
    for row in runs:
        run_id=row["run_id"];observation=get(f"/runs/{run_id}")
        if not observation["events"]:raise ValueError(f"Empty event record {run_id}")
        initial=replay_observation(observation,0)
        agent=next((a for a in agents if a["run_id"]==run_id),None)
        trajectory=get(f"/admin/agents/{agent['id']}/events") if agent else []
        artifacts=[]
        if agent:
            sanitized=LAB/"replays"/agent["id"]
            if not sanitized.exists():raise ValueError("Generate sanitized replays with scripts/package_project.py first.")
            for path in sorted(sanitized.iterdir()):
                if path.is_file() and path.suffix in (".py",".csv",".md",".json",".jsonl",".log"):
                    dest=out/"artifacts"/agent["id"]/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
                    artifacts.append({"name":path.name,"url":f"data/artifacts/{agent['id']}/{path.name}"})
        landscapes=get(f"/admin/landscape/{run_id}") if observation["status"]=="submitted" else []
        write(out/f"runs/{run_id}.json",{"observation":observation,"initial":initial,"agent":agent,"trajectory":trajectory,"landscapes":landscapes,"artifacts":artifacts})
        index.append({**row,"seed":observation["seed"],"agent_status":agent["status"] if agent else None,"events":len(observation["events"]),"url":f"data/runs/{run_id}.json"})
    write(out/"index.json",index)
for name in ("model-validation.json","data-audit.json","baseline-results.json","agent-results.json","system-validation.json"):
    write(out/name,json.loads((LAB/"docs"/name).read_text()))
for name in ("DATA_AND_MODEL.md","BENCHMARK.md","EXAMPLE_TRACE.md"):
    shutil.copyfile(LAB/"docs"/name,out/name)
write(out/"sources.json",json.loads((LAB/"data/source/manifest.json").read_text()))
# Reject accidental credentials before anything is committed or published.
import sqlite3,re
with sqlite3.connect(LAB/"runtime/lab.sqlite3") as db:tokens=[row[0].encode() for row in db.execute("SELECT token FROM runs")]
tokens.append(headers["X-Operator-Key"].encode())
for path in out.rglob("*"):
    if path.is_file():
        data=path.read_bytes()
        if any(token in data for token in tokens):raise ValueError(f"Credential found in public export: {path.name}")
        if re.search(rb'(?:sk-proj-|ghp_|github_pat_)[A-Za-z0-9_]{20,}',data):raise ValueError(f"Possible provider credential in {path.name}")
print(f"Exported {len(index)} runs, {len(agents)} agent trajectories; credential scan passed.")
