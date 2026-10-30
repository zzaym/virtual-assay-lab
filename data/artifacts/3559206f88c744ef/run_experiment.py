import csv
import asyncio
import json
from pathlib import Path
from lab_client import LabClient
from lab_instruments import detect_and_read

lab = LabClient()

stocks = {
    2433: ['A1','A2','A3','A4','A5','A6','A7'],
    2434: ['A8','A9','A10','A11','A12','A13','A14'],
    2429: ['A15','A16','A17','A18','A19','A20','A21'],
    2435: ['A22','A23','A24','B1','B2','B3','B4'],
    2428: ['B5','B6','B7','B8','B9','B10','B11'],
    2430: ['B12','B13','B14','B15','B16','B17','B18'],
    2431: ['B19','B20','B21','B22','B23','B24','C1'],
    2574: ['C2','C3','C4','C5','C6','C7','C8'],
}
pairs = [(2433,2434),(2429,2435),(2428,2429),(2430,2434),(2430,2431),(2431,2574)]
levels = [1, 3, 5]

def well(i):
    row = 'ABCDEFGH'[i // 12]
    return f'{row}{i % 12 + 1}'

rows = []
groups = {'combination': [], 'single_a': [], 'single_b': [], 'vehicle': [], 'blank': []}
idx = 0
for a, b in pairs:
    for li in levels:
        w = well(idx); idx += 1; groups['combination'].append(w)
        rows += [('stocks','384LDV_DMSO',stocks[a][li],'P1',w,7.5),
                 ('stocks','384LDV_DMSO',stocks[b][li],'P1',w,7.5)]
    for li in levels:
        w = well(idx); idx += 1; groups['single_a'].append(w)
        rows += [('stocks','384LDV_DMSO',stocks[a][li],'P1',w,7.5),
                 ('stocks','384LDV_DMSO','P24','P1',w,7.5)]
    for li in levels:
        w = well(idx); idx += 1; groups['single_b'].append(w)
        rows += [('stocks','384LDV_DMSO',stocks[b][li],'P1',w,7.5),
                 ('stocks','384LDV_DMSO','P24','P1',w,7.5)]
for _ in range(12):
    w = well(idx); idx += 1; groups['vehicle'].append(w)
    rows.append(('stocks','384LDV_DMSO','P24','P1',w,15.0))
for _ in range(12):
    w = well(idx); idx += 1; groups['blank'].append(w)

path = Path('screen_picklist.csv')
with path.open('w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['Source Plate Name','Source Plate Type','Source Well','Destination Plate Name','Destination Well','Transfer Volume'])
    out.writerows(rows)

lab.step('create_plate', wells=[well(i) for i in range(96)], blank_wells=groups['blank'],
         rationale='Three-level screen of all six supported pairs with matched single drugs, vehicles, and blanks.')
print('dry_run', lab.echo(path, 'Validate screen picklist and DMSO balance.', dry_run=True))
print('echo', lab.echo(path, 'Execute three-level screen with 15 nL total DMSO per cell-containing well.'))
print('incubate', lab.step('incubate', plate_id='P1', hours=72, temperature_C=37, co2_percent=5,
                         rationale='Standard 72 hour A375 viability exposure.'))
raw = asyncio.run(detect_and_read(lab, 'P1'))
Path('screen_raw.json').write_text(json.dumps(raw, indent=2))
lab.save_observation('screen_observation.json')
print('read_complete', raw[0]['time'])
