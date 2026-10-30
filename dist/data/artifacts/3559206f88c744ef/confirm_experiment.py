import csv, asyncio, json
from pathlib import Path
from lab_client import LabClient
from lab_instruments import detect_and_read

lab = LabClient()
def well(i): return f'{chr(65+i//12)}{i%12+1}'
groups = {k:[well(i*6+j) for j in range(6)] for i,k in enumerate(['combination','single_a','single_b','vehicle','blank'])}
rows=[]
for w in groups['combination']:
    rows += [('stocks','384LDV_DMSO','A20','P2',w,7.5), ('stocks','384LDV_DMSO','B2','P2',w,7.5)]
for w in groups['single_a']:
    rows += [('stocks','384LDV_DMSO','A20','P2',w,7.5), ('stocks','384LDV_DMSO','P24','P2',w,7.5)]
for w in groups['single_b']:
    rows += [('stocks','384LDV_DMSO','B2','P2',w,7.5), ('stocks','384LDV_DMSO','P24','P2',w,7.5)]
for w in groups['vehicle']:
    rows.append(('stocks','384LDV_DMSO','P24','P2',w,15.0))
path=Path('confirmation_picklist.csv')
with path.open('w',newline='') as f:
    out=csv.writer(f);out.writerow(['Source Plate Name','Source Plate Type','Source Well','Destination Plate Name','Destination Well','Transfer Volume']);out.writerows(rows)
allw=[well(i) for i in range(30)]
lab.step('create_plate',wells=allw,blank_wells=groups['blank'],rationale='Independent six-replicate confirmation of D2429+D2435 at the selected screen dose, with matched singles and controls.')
print(lab.echo(path,'Validate confirmation picklist and solvent balance.',dry_run=True))
print(lab.echo(path,'Execute independent confirmation at the selected matched dose.'))
print(lab.step('incubate',plate_id='P2',hours=72,temperature_C=37,co2_percent=5,rationale='Standard 72 hour A375 viability exposure for independent confirmation.'))
raw=asyncio.run(detect_and_read(lab,'P2'));Path('confirmation_raw.json').write_text(json.dumps(raw,indent=2));lab.save_observation('confirmation_observation.json');print('read_complete',raw[0]['time'])
print(json.dumps(groups))
