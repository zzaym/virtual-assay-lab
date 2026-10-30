export function reconstruct(bundle,cutoff){
  const latest=bundle.observation;
  if(!Number.isInteger(cutoff)||cutoff<0||cutoff>=latest.events.length)throw new Error('Invalid replay cursor');
  const state=structuredClone(bundle.initial);
  state.events=[];
  const activate=w=>{if(!w.used){w.used=true;state.wells_used++;}};
  for(const e of latest.events.slice(0,cutoff+1)){
    state.simulated_hours=e.simulated_hours;
    const plate=state.plates[e.plate];
    switch(e.type){
      case 'reset':break;
      case 'plate_created':
        state.plates[e.plate]={name:e.plate,stage:'prepared',created_after_reads:Object.values(state.plates).filter(p=>p.stage==='read').length,wells:Object.fromEntries(e.wells.map(w=>[w,{blank:e.blank_wells.includes(w),volume_uL:state.rules.initial_media_uL,dmso_nL:0,amounts_uM_uL:{},used:false,ctg:false,rlu:null}]))};break;
      case 'echo_protocol':state.phase='Executing protocol';break;
      case 'echo_transfer':{
        const w=plate.wells[e.well],s=state.stocks[e.source],v=e.volume_nL/1000;activate(w);s.volume_uL-=v;w.volume_uL+=v;w.dmso_nL+=e.volume_nL;
        if(s.drug!==null)w.amounts_uM_uL[s.drug]=(w.amounts_uM_uL[s.drug]||0)+s.concentration_uM*e.volume_nL/1000;
        break;}
      case 'incubated':plate.stage='incubated';state.phase='Awaiting detection reagent';break;
      case 'detection_dispense':{const w=plate.wells[e.well];activate(w);w.ctg=true;w.volume_uL+=e.volume_uL;state.ctg_inventory_uL-=e.volume_uL;break;}
      case 'detection_ready':plate.stage='ready_to_read';state.phase='Ready to read';break;
      case 'plate_read':for(const [name,w]of Object.entries(plate.wells))w.rlu=latest.plates[e.plate].wells[name].rlu;plate.stage='read';state.phase='Analyzing results';break;
      case 'submission':state.result=structuredClone(e.result);state.status='submitted';state.phase='Completed';break;
      default:throw new Error(`Unsupported event ${e.type}`);
    }
    state.events.push(e);
  }
  state.remaining_wells=state.rules.total_wells-state.wells_used;state.remaining_plates=state.rules.max_plates-Object.keys(state.plates).length;
  return state;
}
export function label(e){return `${e.sequence} · ${e.simulated_hours.toFixed(2)} h · ${e.type}${e.plate?' · '+e.plate:''}${e.well?' / '+e.well:''}`;}
export function position(name){const [,letters,number]=name.match(/^([A-Z]+)(\d+)$/);return [letters.length===1?letters.charCodeAt(0)-65:26+letters.charCodeAt(1)-65,Number(number)];}
export function measurements(state){
  const rows=[];
  for(const [pid,p]of Object.entries(state.plates)){
    const wells=Object.entries(p.wells).filter(([,w])=>w.rlu!==null);
    const mean=items=>items.length?items.reduce((a,b)=>a+b,0)/items.length:null;
    const blank=mean(wells.filter(([,w])=>w.blank).map(([,w])=>w.rlu));
    const vehicle=mean(wells.filter(([,w])=>!w.blank&&!Object.keys(w.amounts_uM_uL).length).map(([,w])=>w.rlu));
    for(const [name,w]of wells){
      const doses=Object.fromEntries(Object.entries(w.amounts_uM_uL).map(([d,a])=>[d,a/(w.volume_uL-2.5)]));
      const kind=w.blank?'Blank':!Object.keys(doses).length?'Vehicle':Object.keys(doses).length===1?'Single agent':'Combination';
      rows.push({plate:pid,well:name,rlu:w.rlu,kind,doses,inhibition:blank!==null&&vehicle!==null&&vehicle>blank?1-(w.rlu-blank)/(vehicle-blank):null});
    }
  }
  return rows;
}
