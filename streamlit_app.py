"""English operator dashboard; every chart consumes the same public run observation."""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from assay_replay import replay_observation,event_label,trajectory_at_cutoff
from archive_store import read_archive as api,bundle

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title="Virtual Assay Lab",page_icon="🧪",layout="wide")

st.title("Virtual Assay Lab")
st.caption("Data-calibrated cell viability experiments · real instrument interfaces · simulated biology")
health=api("/health")

with st.sidebar:
    st.subheader("Experiment archive")
    st.caption("Read-only replay · no agent execution")
    st.caption("Browse the original recorded experiments, protocols, raw measurements and agent trajectories. No login or model credentials are needed.")
    st.caption("3 plates × up to 96 experimental wells. Each physical plate holds 1,536 wells. All controls and repeats count toward the 288-well budget.")
    st.divider()
    st.metric("Accepted assay scenes",health["accepted_scenes"])
    with st.expander("Model validation"):
        report=api("/admin/validation")
        st.write(f"Internal-dose MAE: {report['test_interpolation_mae']:.3f}")
        st.write(f"90% interval coverage: {report['test_coverage_90']:.1%}")
        st.caption(report["selection_note"])


def well_position(name):
    label="".join(c for c in name if c.isalpha());col=int("".join(c for c in name if c.isdigit()))
    row=ord(label)-65 if len(label)==1 else 26+ord(label[1])-65
    return row,col

def replay_jump(position_key,playing_key,position):
    st.session_state[position_key]=position;st.session_state[playing_key]=False


def replay_pause(playing_key):st.session_state[playing_key]=False


def replay_play(position_key,playing_key,tick_key,last):
    if st.session_state[position_key]>=last:st.session_state[position_key]=0
    st.session_state[playing_key]=True;st.session_state[tick_key]=time.monotonic()+1


def replay_milestone(choice_key,position_key,playing_key):
    choice=st.session_state[choice_key]
    if choice is not None:replay_jump(position_key,playing_key,choice)
    st.session_state[choice_key]=None


def replay_controls(latest,run_id):
    position_key=f"cursor-{run_id}";playing_key=f"playing-{run_id}";tick_key=f"tick-{run_id}"
    mode=st.radio("View mode",["Replay","Final snapshot"],horizontal=True,key=f"mode-{run_id}",on_change=replay_pause,args=(playing_key,))
    if mode=="Final snapshot":return latest,None
    events=latest["events"];last=len(events)-1
    st.session_state.setdefault(position_key,last);st.session_state.setdefault(playing_key,False)
    speed=st.select_slider("Playback speed (events per second)",[1,5,20],value=5,key=f"speed-{run_id}")
    if st.session_state[playing_key] and time.monotonic()>=st.session_state.get(tick_key,0):
        st.session_state[position_key]=min(last,st.session_state[position_key]+speed)
        st.session_state[tick_key]=time.monotonic()+1
        if st.session_state[position_key]==last:st.session_state[playing_key]=False
    position=st.session_state[position_key]
    controls=st.columns(5)
    controls[0].button("First",key=f"first-{run_id}",on_click=replay_jump,args=(position_key,playing_key,0),disabled=position==0)
    controls[1].button("Previous",key=f"previous-{run_id}",on_click=replay_jump,args=(position_key,playing_key,max(0,position-1)),disabled=position==0)
    if st.session_state[playing_key]:
        controls[2].button("Pause",key=f"pause-{run_id}",on_click=replay_jump,args=(position_key,playing_key,position))
    else:
        controls[2].button("Play",key=f"play-{run_id}",on_click=replay_play,args=(position_key,playing_key,tick_key,last),disabled=last==0)
    controls[3].button("Next",key=f"next-{run_id}",on_click=replay_jump,args=(position_key,playing_key,min(last,position+1)),disabled=position==last)
    controls[4].button("Last",key=f"last-{run_id}",on_click=replay_jump,args=(position_key,playing_key,last),disabled=position==last)
    if last:
        st.slider("Laboratory event timeline",min_value=0,max_value=last,key=position_key,on_change=replay_pause,args=(playing_key,),help="Drag through the exact recorded event order. Several transfers share the same simulated time.")
    milestones=[i for i,e in enumerate(events) if e["type"] in ("reset","plate_created","incubated","plate_read","submission")]
    choice_key=f"milestone-{run_id}"
    st.selectbox("Jump to milestone",[None,*milestones],format_func=lambda i:"Choose a plate / read / submission" if i is None else event_label(events[i]),key=choice_key,
                 on_change=replay_milestone,args=(choice_key,position_key,playing_key))
    position=st.session_state[position_key];event=events[position]
    st.info(f"REPLAY · {event_label(event)} · {'Playing' if st.session_state[playing_key] else 'Paused'}")
    if event.get("rationale"):st.write(f"**Experiment rationale:** {event['rationale']}")
    if event["type"]=="echo_transfer":st.write(f"**Transfer:** stocks/{event['source']} → {event['plate']}/{event['well']} · {event['volume_nL']:g} nL")
    st.caption("Historical state reconstructed from recorded operations; playback never executes tools or consumes budget. Playback speed follows event order, not wall-clock experimental duration.")
    return replay_observation(latest,position),position


@st.fragment(run_every="1s")
def monitor():
    runs=api("/admin/runs");agents=api("/admin/agents")
    if not runs:st.info("No archived experiments are available.");return
    ids=[r["run_id"] for r in runs]
    selected=st.session_state.get("selected_run",st.query_params.get("run","84087f9291274421"));index=ids.index(selected) if selected in ids else 0
    run_id=st.selectbox("Experiment / replay",ids,index=index,key="experiment_selector",format_func=lambda x:next(f"{r['label']} · {r['cell']} · {r['status']} · {x}" for r in runs if r["run_id"]==x))
    st.session_state.selected_run=run_id
    latest=api(f"/runs/{run_id}")
    obs,cutoff=replay_controls(latest,run_id)
    agent=next((j for j in agents if j["run_id"]==run_id),None)
    a,b,c,d=st.columns(4)
    a.metric("Experimental wells",f"{obs['wells_used']} / 288")
    b.metric("Plates",f"{len(obs['plates'])} / 3")
    c.metric("Simulated time",f"{obs['simulated_hours']:.1f} h")
    d.metric("Simulator score",f"{obs['result']['score']:.2f}" if obs["result"] else "Pending")
    st.progress(obs["wells_used"]/288,text=f"{obs['remaining_wells']} experimental wells remaining; controls and replicates included")
    st.write(f"**Laboratory:** {obs['phase']}  ·  **Cell:** {obs['cell']}")
    if agent and cutoff is None:
        st.write(f"**Agent:** {agent['status']}  ·  **Last activity:** {agent['last_activity']}")
        if agent["error"]:st.error(agent["error"])
    tabs=st.tabs(["Experiment","Analysis","Trajectory","Protocol & replay","Results"])
    with tabs[0]:
        st.caption("Workflow visualization of executed transfers. No physical robot is connected; geometry and movement are not simulated.")
        stocks=pd.DataFrame([{"source_well":w,**s} for w,s in obs["stocks"].items()])
        st.subheader("Source inventory")
        stocks["row"]=[well_position(w)[0] for w in stocks.source_well]
        stocks["column"]=[well_position(w)[1] for w in stocks.source_well]
        source_fig=px.scatter(stocks,x="column",y="row",color="volume_uL",hover_data=["source_well","label","concentration_uM"],range_color=[3,10])
        source_fig.update_traces(marker={"symbol":"square","size":13})
        source_fig.update_layout(height=220,xaxis={"range":[0,25]},yaxis={"range":[16,-1],"title":"Source row"})
        st.plotly_chart(source_fig,width="stretch")
        st.dataframe(stocks[["source_well","label","drug","concentration_uM","volume_uL","dead_volume_uL"]],hide_index=True,height=180)
        if obs["plates"]:
            plate_key=f"plate-{run_id}";focus_key=f"focus-{run_id}"
            if st.session_state.get(plate_key) not in obs["plates"]:st.session_state[plate_key]=next(reversed(obs["plates"]))
            if cutoff is not None and st.session_state.get(focus_key)!=cutoff:
                focus=latest["events"][cutoff].get("plate")
                if focus in obs["plates"]:st.session_state[plate_key]=focus
                st.session_state[focus_key]=cutoff
            pid=st.selectbox("Assay plate",list(obs["plates"]),key=plate_key);plate=obs["plates"][pid]
            st.write(f"**{pid}: {plate['stage']}** · {len(plate['wells'])} allocated wells / 1,536 physical positions")
            rows=[]
            for well,v in plate["wells"].items():
                row,col=well_position(well)
                pre=v["volume_uL"]-(2.5 if v["ctg"] else 0)
                doses={drug:amount/pre for drug,amount in v["amounts_uM_uL"].items()}
                rows.append({"well":well,"row":row,"column":col,"RLU":v["rlu"],"volume_uL":v["volume_uL"],"blank":v["blank"],"dose_uM":json.dumps(doses),"status":"Measured" if v["rlu"] is not None else ("Detection added" if v["ctg"] else "Dosed" if v["used"] else "Allocated")})
            frame=pd.DataFrame(rows)
            current=obs["events"][-1] if cutoff is not None else {}
            active_well=current.get("well") if current.get("plate")==pid else None
            color="RLU" if frame.RLU.notna().any() else "status"
            fig=px.scatter(frame,x="column",y="row",color=color,hover_data=["well","dose_uM","volume_uL","status"],color_continuous_scale="Viridis")
            fig.update_traces(marker={"size":14,"symbol":"square"})
            if active_well:
                selected=frame[frame.well==active_well]
                fig.add_trace(go.Scatter(x=selected.column,y=selected.row,mode="markers",marker={"size":22,"symbol":"square-open","color":"#EF553B","line":{"width":3}},name="Current event",hoverinfo="skip"))
            fig.update_layout(xaxis={"range":[0,49],"dtick":4},yaxis={"range":[31.8,-.8],"title":"Plate row (A = 0)"},height=450)
            st.plotly_chart(fig,width="stretch")
            st.dataframe(frame.drop(columns=["row","column"]),hide_index=True)
        else:st.info("No assay plate has been created at this point in the timeline.")
        transfers=[e for e in obs["events"] if e["type"]=="echo_transfer"]
        with st.expander(f"Actual transfer log ({len(transfers)} droplets/commands)"):st.dataframe(transfers,hide_index=True)
        for event in obs["events"]:
            if event.get("rationale"):st.write(f"**{event['type']}** — {event['rationale']}")
        if transfers:
            grouped=pd.DataFrame(transfers).groupby(["source","plate"],as_index=False).volume_nL.sum()
            labels=list(dict.fromkeys(list(grouped.source)+list(grouped.plate)))
            links={"source":[labels.index(s) for s in grouped.source],"target":[labels.index(p) for p in grouped.plate],"value":grouped.volume_nL.tolist()}
            fig=go.Figure(go.Sankey(node={"label":labels},link=links));fig.update_layout(title="Executed source → assay transfers (nL)",height=300)
            st.plotly_chart(fig,width="stretch")
    with tabs[1]:
        data=[]
        for pid,p in obs["plates"].items():
            for w,v in p["wells"].items():
                if v["rlu"] is not None:data.append({"plate":pid,"well":w,"RLU":v["rlu"],"kind":"Blank" if v["blank"] else "Vehicle" if not v["amounts_uM_uL"] else "Single agent" if len(v["amounts_uM_uL"])==1 else "Combination","composition":json.dumps({d:amount/(v["volume_uL"]-2.5) for d,amount in v["amounts_uM_uL"].items()})})
        if data:
            frame=pd.DataFrame(data)
            st.plotly_chart(px.box(frame,x="kind",y="RLU",color="plate",points="all",hover_data=["well","composition"]),width="stretch")
            normalized=[]
            for pid,g in frame.groupby("plate"):
                blank=g[g.kind=="Blank"].RLU.mean();vehicle=g[g.kind=="Vehicle"].RLU.mean()
                if np.isfinite(blank) and np.isfinite(vehicle) and vehicle>blank:
                    g=g.copy();g["inhibition"]=1-(g.RLU-blank)/(vehicle-blank);normalized.extend(g.to_dict("records"))
            if normalized:
                nf=pd.DataFrame(normalized);st.plotly_chart(px.scatter(nf,x="well",y="inhibition",color="kind",facet_row="plate",hover_data=["composition"]),width="stretch")
                best=nf[nf.kind=="Combination"].groupby("plate",sort=True).inhibition.max().cummax()
                st.plotly_chart(px.line(x=best.index,y=best.values,markers=True,labels={"x":"Plate","y":"Best observed combination inhibition"}),width="stretch")
                selected_pair=st.selectbox("Measured dose response",obs["pairs"],format_func=lambda p:p["pair_id"],key=f"measured-pair-{run_id}")
                da,db=str(selected_pair["drug_a"]),str(selected_pair["drug_b"])
                measurements=[]
                for row in normalized:
                    composition=json.loads(row["composition"])
                    if composition and set(composition)<={da,db}:
                        measurements.append({**row,"dose_a":composition.get(da,0),"dose_b":composition.get(db,0)})
                if measurements:
                    mf=pd.DataFrame(measurements)
                    curves=[]
                    for drug,col,other in [(da,"dose_a","dose_b"),(db,"dose_b","dose_a")]:
                        for (pid,dose),g in mf[(mf[col]>0)&(mf[other]==0)].groupby(["plate",col]):
                            curves.append({"drug":f"D{drug}","plate":pid,"dose_uM":dose,"inhibition":g.inhibition.mean(),"SEM":g.inhibition.std()/np.sqrt(len(g)) if len(g)>1 else None,"replicates":len(g)})
                    if curves:
                        st.plotly_chart(px.line(pd.DataFrame(curves),x="dose_uM",y="inhibition",color="drug",line_dash="plate",error_y="SEM",markers=True,log_x=True,hover_data=["replicates"]),width="stretch")
                        st.caption("Single-drug curves connect measured points. Error bars are within-plate SEM when repeated wells exist.")
                    combos=mf[(mf.dose_a>0)&(mf.dose_b>0)]
                    if not combos.empty:
                        agg=combos.groupby(["plate","dose_a","dose_b"],as_index=False).inhibition.mean()
                        st.plotly_chart(px.scatter(agg,x="dose_a",y="dose_b",color="inhibition",facet_col="plate",log_x=True,log_y=True,color_continuous_scale="Viridis",range_color=[0,1],size_max=25),width="stretch")
                        hsa=[]
                        for row in agg.to_dict("records"):
                            sa=mf[(mf.plate==row["plate"])&np.isclose(mf.dose_a,row["dose_a"])&(mf.dose_b==0)].inhibition
                            sb=mf[(mf.plate==row["plate"])&np.isclose(mf.dose_b,row["dose_b"])&(mf.dose_a==0)].inhibition
                            if len(sa) and len(sb):hsa.append({**row,"observed_HSA":row["inhibition"]-max(sa.mean(),sb.mean())})
                        if hsa:
                            st.plotly_chart(px.scatter(pd.DataFrame(hsa),x="dose_a",y="dose_b",color="observed_HSA",facet_col="plate",log_x=True,log_y=True,color_continuous_scale="RdBu_r",color_continuous_midpoint=0),width="stretch")
                            st.caption("Observed HSA is shown only where matched-dose single drugs were measured on the same plate. Unmeasured coordinates remain empty.")
        else:st.info("Raw measurements and control-normalized responses appear after the first plate read.")
        st.caption("Raw well distributions include assay noise. Within-plate replication does not establish biological reproducibility. Agent-generated analyses are included in its workspace and trajectory.")
    with tabs[2]:
        if cutoff is not None:
            st.subheader("Laboratory events up to cursor")
            st.dataframe([{k:e[k] for k in ("sequence","simulated_hours","type","plate","well","rationale") if k in e} for e in obs["events"]],hide_index=True)
        if agent:
            events=api(f"/admin/agents/{agent['id']}/events")
            if cutoff is not None:
                filtered=trajectory_at_cutoff(events,latest["events"][cutoff])
                if filtered is None:
                    st.caption("This legacy run has no laboratory wall-clock timestamps. Its laboratory state replays exactly, but agent messages cannot be reliably synchronized to the cursor.")
                    events=events if st.checkbox("Show complete agent trajectory (not synchronized)",key=f"legacy-trajectory-{run_id}") else []
                else:events=filtered;st.caption("Agent trajectory is filtered to the selected laboratory event's wall-clock timestamp.")
            st.caption(f"{len(events)} recorded provider events, including tool commands and outputs. Private model reasoning is not exposed.")
            for i,record in enumerate(events):
                event=record["event"];item=event.get("item",{})
                title=f"{record['received_at']} · {event.get('type','event')} · {item.get('type','')}"
                if item.get("type")=="agent_message":st.markdown(item.get("text",""))
                else:
                    with st.expander(title,expanded=False):st.json(event,expanded=2)
        else:st.info("This run was created through the SDK or a baseline. Laboratory events are available in replay.")
    with tabs[3]:
        st.download_button("Download full experiment replay",json.dumps(latest,indent=2),file_name=f"assay-{run_id}.json",mime="application/json",key=f"replay-{run_id}")
        if cutoff is not None:st.download_button("Download state at cursor",json.dumps(obs,indent=2),file_name=f"assay-{run_id}-event-{cutoff}.json",mime="application/json",key=f"snapshot-{run_id}")
        for i,event in enumerate(obs["events"]):
            if event["type"]=="echo_protocol":
                st.download_button(f"Download Echo protocol {i}",event["picklist_csv"],file_name=f"{run_id}-echo-{i}.csv",key=f"echo-{run_id}-{i}")
        with st.expander("Agent code, analysis files and full trajectory"):
            for artifact in bundle(run_id)["artifacts"]:
                path=(ROOT/artifact["url"]).resolve()
                if not path.is_relative_to((ROOT/"data/artifacts").resolve()):raise ValueError("Artifact path escapes the archive.")
                st.download_button(artifact["name"],path.read_bytes(),file_name=artifact["name"],key=f"artifact-{run_id}-{artifact['name']}")
        with st.expander("Data provenance and validation reports"):
            for name in ("DATA_AND_MODEL.md","BENCHMARK.md","EXAMPLE_TRACE.md","sources.json","model-validation.json","data-audit.json"):
                st.download_button(name,(ROOT/"data"/name).read_bytes(),file_name=name,key=f"report-{run_id}-{name}")
        st.json(obs,expanded=False)
    with tabs[4]:
        if obs["result"]:
            result=obs["result"]
            if not result.get("no_hit"):
                st.write(f"**Confirmed candidate:** {result['pair_id']} · {result['dose_a_uM']:.4g} + {result['dose_b_uM']:.4g} uM")
                st.write(f"**Observed HSA:** {result['observed_hsa_benefit']:.1%} · **95% interval:** [{result['observed_hsa_ci95'][0]:.1%}, {result['observed_hsa_ci95'][1]:.1%}] · **Expected combination inhibition:** {result['expected_combination_inhibition']:.1%}")
            with st.expander("Full result details"):st.json(result,expanded=False)
            st.caption("Hidden simulator surfaces are revealed only after final submission. These are model predictions, not additional wet-lab data.")
            surfaces=api(f"/admin/landscape/{run_id}")
            pair_ids=[s["pair_id"] for s in surfaces]
            pair=st.selectbox("Completed-run response surface",pair_ids,index=pair_ids.index(result["pair_id"]) if result.get("pair_id") in pair_ids else 0,key=f"surface-{run_id}")
            s=next(s for s in surfaces if s["pair_id"]==pair)
            left,right=st.columns(2)
            for column,key,title in [(left,"inhibition","Expected combination inhibition"),(right,"hsa","Expected HSA benefit")]:
                fig=go.Figure(go.Heatmap(x=s["dose_a"],y=s["dose_b"],z=s[key],colorbar={"title":key}))
                fig.update_layout(title=title,xaxis_type="log",yaxis_type="log",xaxis_title="Drug A (uM)",yaxis_title="Drug B (uM)")
                column.plotly_chart(fig,width="stretch")
        else:st.info("Final score, confirmation uncertainty and hidden surfaces are available after submission.")
        baseline_path=ROOT/"data/baseline-results.json";agent_path=ROOT/"data/agent-results.json"
        if baseline_path.exists() and obs["result"]:
            st.subheader("Fixed-seed benchmark")
            records=[{"seed":r["seed"],"policy":r["policy"],"score":r["score"],"wells":r["wells_used"],"run_id":r["run_id"]} for r in json.loads(baseline_path.read_text())]
            if agent_path.exists():
                for r in json.loads(agent_path.read_text()):
                    records.append({"seed":r["seed"],"policy":"Codex GPT-5.6 Luna","score":r["result"]["score"] if r["result"] else None,"wells":r["wells_used"],"run_id":r["job"]["run_id"]})
            bf=pd.DataFrame(records)
            st.dataframe(bf.pivot(index="seed",columns="policy",values="score"),hide_index=False)
            st.plotly_chart(px.bar(bf[bf.seed.isin([42,43,44])],x="seed",y="score",color="policy",barmode="group",hover_data=["wells","run_id"]),width="stretch")
            st.caption("Same world seed, supported doses, protocol format and 288-well cap. Baselines use 282 wells; agent may stop earlier or report no hit. Three agent seeds support a demonstration, not a performance claim.")

monitor()
