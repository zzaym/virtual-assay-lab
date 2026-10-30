import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {reconstruct} from '../dist/replay.js';

const root=fileURLToPath(new URL('../',import.meta.url));
const python=spawnSync(root+'../virtual-biolab/.venv/bin/python',['-c',`
import sys,json,pathlib
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root.parent/'virtual-biolab'))
from virtual_assay.replay import replay_observation
golden={}
for p in (root/'dist/data/runs').glob('*.json'):
 b=json.loads(p.read_text());o=b['observation'];indices={0,len(o['events'])-1}
 indices.update(i for i,e in enumerate(o['events']) if e['type'] in ['plate_created','incubated','plate_read','submission'])
 indices.update(next((i for i,e in enumerate(o['events']) if e['type']==t),0) for t in ['echo_transfer','detection_dispense','detection_ready'])
 golden[p.stem]={}
 for i in sorted(indices):
  state=replay_observation(o,i);del state['events'];golden[p.stem][i]=state
print(json.dumps(golden))
`,root],{encoding:'utf8',maxBuffer:128*1024*1024});
assert.equal(python.status,0,python.stderr);const golden=JSON.parse(python.stdout);
function equal(a,b,path='state'){
  if(typeof a==='number'&&typeof b==='number'){assert.ok(Math.abs(a-b)<=1e-10*Math.max(1,Math.abs(b)),`${path}: ${a} != ${b}`);return;}
  if(a&&b&&typeof a==='object'&&typeof b==='object'){
    assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),path);
    for(const k of Object.keys(a))equal(a[k],b[k],path+'.'+k);return;
  }
  assert.equal(a,b,path);
}
let count=0;
for(const name of readdirSync(root+'dist/data/runs')){
  const b=JSON.parse(readFileSync(root+'dist/data/runs/'+name));
  for(const [cutoff,expected]of Object.entries(golden[name.slice(0,-5)])){const actual=reconstruct(b,Number(cutoff));assert.equal(actual.events.length,Number(cutoff)+1);delete actual.events;equal(actual,expected,name+'.'+cutoff);count++;}
  let read=false;
  for(let i=0;i<b.observation.events.length;i++){
    const e=b.observation.events[i];if(e.type==='plate_read')read=true;
    const s=reconstruct(b,i);
    if(!read)assert.ok(Object.values(s.plates).every(p=>Object.values(p.wells).every(w=>w.rlu===null)));
    if(e.type!=='submission')assert.equal(s.result,null);
  }
}
console.log(`PASS: ${Object.keys(golden).length} runs, ${count} Python/JavaScript snapshot comparisons; all prefixes hide future readings and scores.`);
