import csv, asyncio, json
from pathlib import Path
from lab_client import LabClient
from lab_instruments import detect_and_read
lab=LabClient()
def well(i): return f'{chr(65+i//12)}{i%12+1}'
g={k:[well(i*6+j) for j in range(6)] for i,k in enumerate(['combination','single_a','single_b','vehicle','blank'])}
rows=[]
for w in g['combination']: rows += [('stocks','384LDV_DMSO','B18','P3',w,7.5),('stocks','384LDV_DMSO','C1','P3',w,7.5)]
for w in g['single_a']: rows += [('stocks','384LDV_DMSO','B18','P3',w,7.5),('stocks','384LDV_DMSO','P24','P3',w,7.5)]
for w in g['single_b']: rows += [('stocks','384LDV_DMSO','C1','P3',w,7.5),('stocks','384LDV_DMSO','P24','P3',w,7.5)]
for w in g['vehicle']: rows.append(('stocks','384LDV_DMSO','P24','P3',w,15.0))
p=Path('confirmation2_picklist.csv')
with p.open('w',newline='') as f:
 o=csv.writer(f);o.writerow(['Source Plate Name','Source Plate Type','Source Well','Destination Plate Name','Destination Well','Transfer Volume']);o.writerows(rows)
lab.step('create_plate',wells=[well(i) for i in range(30)],blank_wells=g['blank'],rationale='Final independent six-replicate confirmation of D2430+D2431 at the selected high matched dose.')
print(lab.echo(p,'Validate final confirmation picklist.',dry_run=True));print(lab.echo(p,'Execute final independent confirmation with matched DMSO.'))
print(lab.step('incubate',plate_id='P3',hours=72,temperature_C=37,co2_percent=5,rationale='Standard 72 hour A375 viability exposure for final confirmation.'))
raw=asyncio.run(detect_and_read(lab,'P3'));Path('confirmation2_raw.json').write_text(json.dumps(raw,indent=2));lab.save_observation('confirmation2_observation.json');print('read_complete',raw[0]['time']);print(json.dumps(g))
