import {reconstruct,label,position,measurements} from './replay.js';
const $=id=>document.getElementById(id),clone=x=>structuredClone(x),fmt=(n,d=2)=>Number(n).toFixed(d),pct=n=>`${fmt(n*100,1)}%`;
let index=[],bundle,state,cursor=0,timer=null,tab='lab',benchmarks=[],agentResults=[];
const config={responsive:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']};
const layout={font:{family:'system-ui,sans-serif',size:11,color:'#4e6470'},paper_bgcolor:'transparent',plot_bgcolor:'#fbfcfd',margin:{l:55,r:35,t:45,b:50},colorway:['#087f8c','#d68d36','#6977ad','#a24a68','#68996a']};
function plot(id,data,title,extra={}){Plotly.react($(id),data,{...clone(layout),title:{text:title,font:{size:14}},...extra},config);}
function empty(id,message){Plotly.purge($(id));$(id).replaceChildren();const el=document.createElement('p');el.className='empty';el.textContent=message;$(id).append(el);}
function text(id,value){$(id).textContent=value;}
function table(id,rows,columns){
  const host=$(id);host.replaceChildren();if(!rows.length){host.textContent='No records at this point.';return;}
  const t=document.createElement('table'),head=t.createTHead().insertRow();
  for(const c of columns){const th=document.createElement('th');th.textContent=c;head.append(th);}
  const body=t.createTBody();for(const row of rows){const tr=body.insertRow();for(const c of columns){const td=tr.insertCell();const v=row[c];td.textContent=v===undefined?'':typeof v==='object'?JSON.stringify(v):String(v);}}
  host.append(t);
}
function options(id,items,preferred){
  const s=$(id),old=s.value;s.replaceChildren();for(const [value,name]of items){const o=document.createElement('option');o.value=value;o.textContent=name;s.append(o);}
  s.value=items.some(([v])=>v===preferred)?preferred:items.some(([v])=>v===old)?old:items[0]?.[0]||'';
}
async function json(path){const r=await fetch(path);if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.json();}
function fail(error){pause();$('error').hidden=false;text('error',`Unable to display this archive: ${error.message}`);console.error(error);}
function pause(){if(timer)clearInterval(timer);timer=null;text('play','Play');}
function setCursor(value){cursor=Math.max(0,Math.min(bundle.observation.events.length-1,Number(value)));state=reconstruct(bundle,cursor);render();}
async function loadRun(){
  pause();$('error').hidden=true;
  const row=index.find(r=>r.run_id===$('run').value);bundle=await json(row.url);cursor=bundle.observation.events.length-1;
  const url=new URL(location);url.searchParams.set('run',row.run_id);history.replaceState(null,'',url);
  $('download').href=row.url;$('download').download=`assay-${row.run_id}.json`;
  $('timeline').max=cursor;
  options('milestone',[['','Choose a plate / read / submission'],...bundle.observation.events.filter(e=>['reset','plate_created','incubated','plate_read','submission'].includes(e.type)).map(e=>[String(e.sequence),label(e)])],'');
  options('pair',bundle.observation.pairs.map(p=>[p.pair_id,`${p.compound_a?.name||'D'+p.drug_a} + ${p.compound_b?.name||'D'+p.drug_b} (${p.pair_id})`]));
  options('surface',bundle.landscapes.map(p=>[p.pair_id,p.pair_id]),bundle.observation.result?.pair_id);
  $('full-trajectory').checked=false;setCursor(cursor);
}
function render(){
  const e=state.events.at(-1);$('timeline').value=cursor;text('cursor',`${cursor} / ${bundle.observation.events.length-1}`);
  text('event',`${label(e)}${e.type==='echo_transfer'?` · stocks/${e.source} → ${e.plate}/${e.well} · ${e.volume_nL} nL`:''}${e.rationale?' — '+e.rationale:''}`);
  text('wells',`${state.wells_used} / 288`);text('plates',`${Object.keys(state.plates).length} / 3`);text('hours',`${fmt(state.simulated_hours,1)} h`);text('score',state.result?fmt(state.result.score):'Pending');
  text('phase',state.phase);text('identity',`${state.cell} · seed ${state.seed} · ${state.run_id}`);
  $('first').disabled=$('prev').disabled=cursor===0;$('last').disabled=$('next').disabled=cursor===bundle.observation.events.length-1;
  if(cursor===bundle.observation.events.length-1)pause();
  options('plate',Object.keys(state.plates).map(p=>[p,p]),e.plate);
  renderTab();
}
function renderTab(){
  if(tab==='lab')renderLab();if(tab==='analysis')renderAnalysis();if(tab==='trajectory')renderTrajectory();if(tab==='results')renderResults();
}
function renderLab(){
  const stocks=Object.entries(state.stocks).map(([w,s])=>({source:w,...s}));
  plot('sources',[{type:'scatter',mode:'markers',x:stocks.map(s=>position(s.source)[1]),y:stocks.map(s=>position(s.source)[0]),text:stocks.map(s=>`${s.source} · ${s.label}<br>${fmt(s.concentration_uM,5)} uM<br>${fmt(s.volume_uL,4)} uL`),hovertemplate:'%{text}<extra></extra>',marker:{symbol:'square',size:13,color:stocks.map(s=>s.volume_uL),colorscale:'Teal',cmin:3,cmax:10,colorbar:{title:'uL'}}}],'384-well source plate',{xaxis:{range:[0,25],title:'Column'},yaxis:{range:[16,-1],title:'Row (A = 0)'}});
  table('stock-table',stocks,['source','label','drug','concentration_uM','volume_uL','dead_volume_uL']);
  const pid=$('plate').value,p=state.plates[pid];
  if(!p){text('plate-info','No assay plate has been created.');empty('plate-plot','Move the cursor forward to plate creation.');table('well-table',[],[]);}
  else{
    text('plate-info',`${pid}: ${p.stage} · ${Object.keys(p.wells).length} allocated / 1,536 physical positions`);
    const rows=Object.entries(p.wells).map(([name,w])=>({well:name,...w,dose_uM:Object.fromEntries(Object.entries(w.amounts_uM_uL).map(([d,a])=>[d,a/(w.volume_uL-(w.ctg?2.5:0))]))}));
    const measured=rows.some(w=>w.rlu!==null);
    const current=state.events.at(-1),selected=rows.find(w=>w.well===current.well&&current.plate===pid);
    const traces=[{type:'scatter',mode:'markers',x:rows.map(w=>position(w.well)[1]),y:rows.map(w=>position(w.well)[0]),text:rows.map(w=>`${w.well} · ${w.blank?'blank':w.rlu!==null?'measured':w.ctg?'detection added':w.used?'dosed':'allocated'}<br>${JSON.stringify(w.dose_uM)} uM<br>${fmt(w.volume_uL,4)} uL${w.rlu!==null?'<br>'+fmt(w.rlu,1)+' RLU':''}`),hovertemplate:'%{text}<extra></extra>',marker:{symbol:'square',size:12,color:rows.map(w=>measured?w.rlu:w.ctg?3:w.used?2:1),colorscale:'Viridis',colorbar:{title:measured?'RLU':'Stage'}}}];
    if(selected)traces.push({type:'scatter',mode:'markers',x:[position(selected.well)[1]],y:[position(selected.well)[0]],marker:{symbol:'square-open',size:21,color:'#e66d40',line:{width:3}},name:'Current event',hoverinfo:'skip'});
    plot('plate-plot',traces,'Executed well state',{showlegend:false,xaxis:{range:[0,49],dtick:4,title:'Column'},yaxis:{range:[32,-1],title:'Row (A = 0)'}});
    table('well-table',rows,['well','blank','used','ctg','volume_uL','dose_uM','rlu']);
  }
  const transfers=state.events.filter(e=>e.type==='echo_transfer');table('transfer-table',transfers,['sequence','source','plate','well','volume_nL']);
  if(transfers.length){const totals=new Map();for(const e of transfers){const k=e.source+'|'+e.plate;totals.set(k,(totals.get(k)||0)+e.volume_nL);}const labels=[...new Set(transfers.map(e=>e.source).concat(transfers.map(e=>e.plate)))],entries=[...totals];plot('transfers',[{type:'sankey',node:{label:labels,pad:9,thickness:10},link:{source:entries.map(([k])=>labels.indexOf(k.split('|')[0])),target:entries.map(([k])=>labels.indexOf(k.split('|')[1])),value:entries.map(([,v])=>v)}}],'Actual source → assay transfers (nL)');}else empty('transfers','No liquid transfers have executed.');
  $('reasons').replaceChildren();for(const e of state.events.filter(e=>e.rationale)){const p=document.createElement('p');p.textContent=`${e.sequence} · ${e.type}: ${e.rationale}`;$('reasons').append(p);}
}
function renderAnalysis(){
  const rows=measurements(state),valid=rows.filter(r=>r.inhibition!==null);
  if(!rows.length){for(const id of ['raw','inhibition','best','singles','combo','hsa'])empty(id,'No measured results at this event.');return;}
  const plates=[...new Set(rows.map(r=>r.plate))];
  plot('raw',plates.map(p=>({type:'box',name:p,y:rows.filter(r=>r.plate===p).map(r=>r.rlu),x:rows.filter(r=>r.plate===p).map(r=>r.kind),boxpoints:'all',jitter:.3,pointpos:0})), 'Raw luminescence distributions',{yaxis:{title:'RLU'},boxmode:'group'});
  plot('inhibition',plates.map(p=>({type:'scatter',mode:'markers',name:p,x:valid.filter(r=>r.plate===p).map(r=>r.well),y:valid.filter(r=>r.plate===p).map(r=>r.inhibition),text:valid.filter(r=>r.plate===p).map(r=>`${r.kind}: ${JSON.stringify(r.doses)} uM`),hovertemplate:'%{x}: %{y:.3f}<br>%{text}<extra>%{fullData.name}</extra>'})),'Control-normalized inhibition',{yaxis:{title:'Inhibition'}});
  let running=-Infinity;const best=plates.map(p=>{const values=valid.filter(r=>r.plate===p&&r.kind==='Combination').map(r=>r.inhibition);running=Math.max(running,...values);return Number.isFinite(running)?running:null;});
  plot('best',[{x:plates,y:best,mode:'lines+markers',type:'scatter'}],'Best observed combination inhibition',{yaxis:{title:'Inhibition'}});
  const pair=state.pairs.find(p=>p.pair_id===$('pair').value),a=String(pair.drug_a),b=String(pair.drug_b),selected=valid.filter(r=>Object.keys(r.doses).length&&Object.keys(r.doses).every(d=>d===a||d===b));
  const curves=[];
  for(const p of plates)for(const drug of [a,b]){
    const points=selected.filter(r=>r.plate===p&&Object.keys(r.doses).length===1&&r.doses[drug]);const groups=new Map();
    for(const r of points){const key=r.doses[drug];if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r.inhibition);}
    const sorted=[...groups].sort((x,y)=>x[0]-y[0]);if(sorted.length)curves.push({type:'scatter',mode:'lines+markers',name:`${p} D${drug}`,x:sorted.map(([dose])=>dose),y:sorted.map(([,v])=>v.reduce((s,x)=>s+x,0)/v.length),error_y:{type:'data',array:sorted.map(([,v])=>{const mean=v.reduce((s,x)=>s+x,0)/v.length;return v.length>1?Math.sqrt(v.reduce((s,x)=>s+(x-mean)**2,0)/(v.length-1)/v.length):0;})}});
  }
  if(curves.length)plot('singles',curves,'Measured single-drug dose response',{xaxis:{type:'log',title:'uM'},yaxis:{title:'Inhibition'}});else empty('singles','No single-drug measurements for this pair.');
  const combos=selected.filter(r=>r.doses[a]&&r.doses[b]);
  const surface=(id,points,title)=>points.length?plot(id,[{type:'scatter',mode:'markers',x:points.map(r=>r.doses[a]),y:points.map(r=>r.doses[b]),text:points.map(r=>r.plate+'/'+r.well),marker:{size:15,color:points.map(r=>r.value),colorscale:id==='hsa'?'RdBu':'Viridis',reversescale:id==='hsa',colorbar:{title:id==='hsa'?'HSA':'Inhibition'}},hovertemplate:'%{text}<br>A=%{x:.4g}, B=%{y:.4g}<br>Response=%{marker.color:.3f}<extra></extra>'}],title,{xaxis:{type:'log',title:'Drug A (uM)'},yaxis:{type:'log',title:'Drug B (uM)'}}):empty(id,'No matched measurements available.');
  surface('combo',combos.map(r=>({...r,value:r.inhibition})),'Measured combinations');
  const hsa=[];for(const r of combos){const singles=drug=>selected.filter(s=>s.plate===r.plate&&Object.keys(s.doses).length===1&&s.doses[drug]&&Math.abs(s.doses[drug]/r.doses[drug]-1)<1e-5);const sa=singles(a),sb=singles(b),mean=g=>g.reduce((s,r)=>s+r.inhibition,0)/g.length;if(sa.length&&sb.length)hsa.push({...r,value:r.inhibition-Math.max(mean(sa),mean(sb))});}
  surface('hsa',hsa,'Observed HSA versus matched-dose single agents');
}
function renderTrajectory(){
  const e=state.events.at(-1),all=$('full-trajectory').checked,full=bundle.trajectory;
  const records=all?full:e.timestamp?full.filter(r=>Date.parse(r.received_at)<=Date.parse(e.timestamp)):[];
  text('trajectory-note',!bundle.agent?'Baseline or SDK run: no model-provider trajectory.':e.timestamp?'Messages are filtered to the selected laboratory event timestamp unless complete trajectory is enabled.':'Legacy run: laboratory state replays exactly; wall-clock synchronization of agent messages is unavailable. Enable complete trajectory to inspect the full ordered provider log.');
  $('messages').replaceChildren();
  for(const r of records){const e=r.event,i=e.item||{};
    if(i.type==='agent_message'){const div=document.createElement('div');div.className='message';const time=document.createElement('small');time.textContent=r.received_at;const p=document.createElement('p');p.textContent=i.text;div.append(time,p);$('messages').append(div);}
    else{const details=document.createElement('details'),s=document.createElement('summary'),p=document.createElement('pre');s.textContent=`${r.received_at} · ${e.type} · ${i.type||''}`;p.textContent=JSON.stringify(e,null,2);details.append(s,p);$('messages').append(details);}
  }
  $('artifacts').replaceChildren();for(const artifact of bundle.artifacts){const a=document.createElement('a');a.href=artifact.url;a.textContent=artifact.name;a.download=artifact.name;$('artifacts').append(a);}
  for(const e of state.events.filter(e=>e.type==='echo_protocol')){const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,'+encodeURIComponent(e.picklist_csv);a.download=`echo-event-${e.sequence}.csv`;a.textContent=`Executed Echo picklist · event ${e.sequence}`;$('artifacts').append(a);}
  table('events',state.events.map(e=>({sequence:e.sequence,hours:fmt(e.simulated_hours),type:e.type,plate:e.plate,well:e.well,rationale:e.rationale})),['sequence','hours','type','plate','well','rationale']);
}
function renderResults(){
  const r=state.result;const host=$('result-summary');host.replaceChildren();$('landscape-card').hidden=!r;$('benchmark-card').hidden=!r;
  text('result-json',r?JSON.stringify(r,null,2):'Final submission has not happened at this cursor.');
  if(!r){const p=document.createElement('p');p.textContent='Final recommendation and hidden surfaces remain unavailable until the submission event.';host.append(p);empty('confirmation','Advance to submission for confirmation results.');}
  else{
    const p=document.createElement('p');p.textContent=r.no_hit?r.conclusion:`${r.pair_id}: ${fmt(r.dose_a_uM,4)} + ${fmt(r.dose_b_uM,4)} uM. ${r.conclusion}`;host.append(p);
    const grid=document.createElement('div');grid.className='result-grid';for(const [name,value]of [['Simulator score',fmt(r.score)],['Observed HSA',r.no_hit?'No hit':pct(r.observed_hsa_benefit)],['95% HSA interval',r.no_hit?'—':r.observed_hsa_ci95.map(pct).join(' to ')]]){const d=document.createElement('div'),s=document.createElement('strong');d.textContent=name;s.textContent=value;d.append(s);grid.append(d);}host.append(grid);
    const note=document.createElement('p');note.className='note';note.textContent=r.uncertainty_note;host.append(note);
    if(!r.no_hit)plot('confirmation',[{type:'bar',x:['Combination','Single A','Single B'],y:[r.observed_inhibition.combination,r.observed_inhibition.single_a,r.observed_inhibition.single_b],marker:{color:['#087f8c','#b0bbc0','#788d98']}}],'Observed independent confirmation',{yaxis:{title:'Inhibition'}});else empty('confirmation','No-hit conclusion submitted.');
    const s=bundle.landscapes.find(s=>s.pair_id===$('surface').value);if(s)for(const [id,key,title]of [['surface-i','inhibition','Expected combination inhibition'],['surface-h','hsa','Expected HSA benefit']])plot(id,[{type:'heatmap',x:s.dose_a,y:s.dose_b,z:s[key],colorscale:key==='hsa'?'RdBu':'Viridis',reversescale:key==='hsa',colorbar:{title:key}}],title,{xaxis:{type:'log',title:'Drug A (uM)'},yaxis:{type:'log',title:'Drug B (uM)'}});
  }
  const records=benchmarks.map(r=>({seed:r.seed,policy:r.policy,score:r.score,wells:r.wells_used})).concat(agentResults.map(r=>({seed:r.seed,policy:'Codex GPT-5.6 Luna',score:r.result?.score??null,wells:r.wells_used})));
  table('benchmark-table',records,['seed','policy','score','wells']);
  plot('benchmark-plot',[...new Set(records.map(r=>r.policy))].map(p=>({type:'bar',name:p,x:records.filter(r=>r.policy===p&&r.seed<=44).map(r=>String(r.seed)),y:records.filter(r=>r.policy===p&&r.seed<=44).map(r=>r.score)})),'Shared-seed strategy comparison',{barmode:'group',yaxis:{title:'Simulator score'}});
}
async function init(){
  [index,benchmarks,agentResults]=await Promise.all([json('data/index.json'),json('data/baseline-results.json'),json('data/agent-results.json')]);
  const requested=new URL(location).searchParams.get('run')||'84087f9291274421';
  options('run',index.map(r=>[r.run_id,`${r.label} · ${r.cell} · seed ${r.seed} · ${r.agent_status||r.status} · ${r.run_id}`]),requested);
  $('run').onchange=()=>loadRun().catch(fail);$('timeline').oninput=()=>{pause();setCursor($('timeline').value);};
  $('first').onclick=()=>{pause();setCursor(0);};$('last').onclick=()=>{pause();setCursor(bundle.observation.events.length-1);};$('prev').onclick=()=>{pause();setCursor(cursor-1);};$('next').onclick=()=>{pause();setCursor(cursor+1);};
  $('play').onclick=()=>{if(timer){pause();return;}if(cursor===bundle.observation.events.length-1)setCursor(0);text('play','Pause');timer=setInterval(()=>{try{setCursor(cursor+Number($('speed').value));}catch(e){fail(e);}},1000);};
  $('milestone').onchange=()=>{if($('milestone').value==='')return;pause();setCursor($('milestone').value);$('milestone').value='';};
  $('plate').onchange=renderLab;$('pair').onchange=renderAnalysis;$('surface').onchange=renderResults;$('full-trajectory').onchange=renderTrajectory;
  for(const button of $('tabs').querySelectorAll('button'))button.onclick=()=>{tab=button.dataset.tab;for(const b of $('tabs').querySelectorAll('button'))b.setAttribute('aria-pressed',String(b===button));for(const panel of document.querySelectorAll('.panel'))panel.hidden=panel.id!==tab;renderTab();};
  const report=await json('data/model-validation.json');text('validation',`${report.cases.filter(c=>c.accepted).length} accepted scenes across ${report.eligible_cells.length} cells. Held-out internal-dose MAE: ${fmt(report.test_interpolation_mae*100)} percentage points; 90% interval coverage: ${pct(report.test_coverage_90)}.`);
  for(const file of ['DATA_AND_MODEL.md','BENCHMARK.md','EXAMPLE_TRACE.md','model-validation.json','data-audit.json','baseline-results.json','agent-results.json','system-validation.json','sources.json','index.json']){const a=document.createElement('a');a.href='data/'+file;a.textContent=file;$('reports').append(a);}
  await loadRun();
}
window.addEventListener('error',e=>fail(e.error||new Error(e.message)));init().catch(fail);
