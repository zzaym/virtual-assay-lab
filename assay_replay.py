"""Reconstruct public laboratory state from an event prefix, without re-running biology."""
from __future__ import annotations

import copy


def replay_observation(latest: dict, cutoff: int) -> dict:
    events=latest["events"]
    if not isinstance(cutoff,int) or not 0<=cutoff<len(events):
        raise ValueError("Replay cutoff must identify an existing laboratory event.")
    view=copy.deepcopy(latest)
    view.update(status="active",phase="Ready",simulated_hours=0.,wells_used=0,plates={},events=[],result=None)
    # Undo recorded consumption to recover initial inventories, then apply the prefix.
    # No response model is loaded and no new random measurement is sampled.
    for event in events:
        if event["type"]=="echo_transfer":view["stocks"][event["source"]]["volume_uL"]+=event["volume_nL"]/1000
        elif event["type"]=="detection_dispense":view["ctg_inventory_uL"]+=event["volume_uL"]
    def activate(target):
        if not target["used"]:target["used"]=True;view["wells_used"]+=1
    for event in events[:cutoff+1]:
        kind=event["type"];view["simulated_hours"]=event["simulated_hours"]
        if kind=="reset":pass
        elif kind=="plate_created":
            view["plates"][event["plate"]]={"name":event["plate"],"stage":"prepared",
                "created_after_reads":sum(p["stage"]=="read" for p in view["plates"].values()),
                "wells":{w:{"blank":w in event["blank_wells"],"volume_uL":view["rules"]["initial_media_uL"],
                    "dmso_nL":0.,"amounts_uM_uL":{},"used":False,"ctg":False,"rlu":None} for w in event["wells"]}}
        elif kind=="echo_protocol":view["phase"]="Executing protocol"
        elif kind=="echo_transfer":
            target=view["plates"][event["plate"]]["wells"][event["well"]];source=view["stocks"][event["source"]]
            volume=event["volume_nL"]/1000;activate(target)
            source["volume_uL"]-=volume;target["volume_uL"]+=volume;target["dmso_nL"]+=event["volume_nL"]
            if source["drug"] is not None:
                drug=str(source["drug"])
                target["amounts_uM_uL"][drug]=target["amounts_uM_uL"].get(drug,0)+source["concentration_uM"]*event["volume_nL"]/1000
        elif kind=="incubated":
            view["plates"][event["plate"]]["stage"]="incubated";view["phase"]="Awaiting detection reagent"
        elif kind=="detection_dispense":
            target=view["plates"][event["plate"]]["wells"][event["well"]];activate(target)
            target["ctg"]=True;target["volume_uL"]+=event["volume_uL"];view["ctg_inventory_uL"]-=event["volume_uL"]
        elif kind=="detection_ready":
            view["plates"][event["plate"]]["stage"]="ready_to_read";view["phase"]="Ready to read"
        elif kind=="plate_read":
            plate=view["plates"][event["plate"]]
            for name,target in plate["wells"].items():target["rlu"]=latest["plates"][event["plate"]]["wells"][name]["rlu"]
            plate["stage"]="read";view["phase"]="Analyzing results"
        elif kind=="submission":view.update(status="submitted",phase="Completed",result=copy.deepcopy(event["result"]))
        else:raise ValueError(f"Replay does not support event type {kind!r} at sequence {event['sequence']}.")
        view["events"].append(copy.deepcopy(event))
    view["remaining_wells"]=view["rules"]["total_wells"]-view["wells_used"]
    view["remaining_plates"]=view["rules"]["max_plates"]-len(view["plates"])
    return view


def event_label(event: dict) -> str:
    detail=" · ".join(str(event[k]) for k in ("plate","well") if k in event)
    return f"{event['sequence']} · {event['simulated_hours']:.2f} h · {event['type']}"+(f" · {detail}" if detail else "")


def trajectory_at_cutoff(records: list[dict], event: dict) -> list[dict] | None:
    """None means the legacy lab log has no trustworthy wall-clock synchronization."""
    timestamp=event.get("timestamp")
    if timestamp is None:return None
    from datetime import datetime
    cutoff=datetime.fromisoformat(timestamp)
    return [r for r in records if datetime.fromisoformat(r["received_at"])<=cutoff]
