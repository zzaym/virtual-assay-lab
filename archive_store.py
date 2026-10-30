"""Read-only, local-file data access. No network, credentials, devices or execution API."""
import json
import re
from pathlib import Path

import streamlit as st

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"

@st.cache_data(show_spinner=False)
def read_json(relative):
    path=(DATA/relative).resolve()
    if not path.is_relative_to(DATA.resolve()):raise ValueError("Archive path escapes the data directory.")
    return json.loads(path.read_text())

def bundle(run_id):
    if not re.fullmatch(r"[a-f0-9]{16}",run_id):raise ValueError("Invalid archived run identifier.")
    return read_json(f"runs/{run_id}.json")

@st.cache_data(show_spinner=False)
def archived_agents():
    return [b["agent"] for r in read_json("index.json") if (b:=bundle(r["run_id"]))["agent"]]

def read_archive(path):
    if path=="/health":
        report=read_json("model-validation.json")
        return {"status":"archive","accepted_scenes":sum(r["accepted"] for r in report["cases"]),"cells":report["eligible_cells"]}
    if path=="/admin/runs":return read_json("index.json")
    if path=="/admin/agents":return archived_agents()
    if path=="/admin/validation":return read_json("model-validation.json")
    if match:=re.fullmatch(r"/runs/([a-f0-9]{16})",path):return bundle(match[1])["observation"]
    if match:=re.fullmatch(r"/admin/landscape/([a-f0-9]{16})",path):
        record=bundle(match[1])
        if record["observation"]["status"]!="submitted":raise ValueError("This archived run has no final submission.")
        return record["landscapes"]
    if match:=re.fullmatch(r"/admin/agents/([a-f0-9]{16})/events",path):
        agent=next((a for a in archived_agents() if a["id"]==match[1]),None)
        if agent is None:raise ValueError("Unknown archived agent.")
        return bundle(agent["run_id"])["trajectory"]
    raise ValueError(f"Operation unavailable in read-only archive: {path}")
