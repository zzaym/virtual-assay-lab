from pathlib import Path

header = 'Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Well,Transfer Volume\n'
rows=[]
for w in ['A1','A2','A3']:
    rows += [['stocks','384LDV_DMSO','B6','P3',w,'7.5'],['stocks','384LDV_DMSO','A17','P3',w,'7.5']]
for w in ['A4','A5','A6']:
    rows += [['stocks','384LDV_DMSO','B6','P3',w,'7.5'],['stocks','384LDV_DMSO','P24','P3',w,'7.5']]
for w in ['A7','A8','A9']:
    rows += [['stocks','384LDV_DMSO','A17','P3',w,'7.5'],['stocks','384LDV_DMSO','P24','P3',w,'7.5']]
for w in ['A10','A11','A12']:
    rows.append(['stocks','384LDV_DMSO','P24','P3',w,'15'])
Path('/work/confirmation_picklist.csv').write_text(header+'\n'.join(','.join(r) for r in rows)+'\n')
