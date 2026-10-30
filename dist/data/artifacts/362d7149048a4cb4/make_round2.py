from pathlib import Path

header = 'Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Well,Transfer Volume\n'
conditions = [
    ('B5','A15'),  # low / low
    ('B6','A17'),  # P1 lead dose
    ('B7','A19'),  # high / high
    ('B6','A15'),  # A mid / B low
    ('B5','A17'),  # A low / B mid
    ('B7','A17'),  # A high / B mid
]
def well(n):
    return f"{'A' if n <= 48 else 'B'}{n if n <= 48 else n-48}"
rows=[]
for i,(sa,sb) in enumerate(conditions):
    base=i*11
    combos=[well(base+j+1) for j in range(3)]
    singles_a=[well(base+j+4) for j in range(3)]
    singles_b=[well(base+j+7) for j in range(3)]
    vehicle=well(base+10)
    for w in combos:
        rows += [["stocks","384LDV_DMSO",sa,"P2",w,"7.5"],["stocks","384LDV_DMSO",sb,"P2",w,"7.5"]]
    for w in singles_a:
        rows += [["stocks","384LDV_DMSO",sa,"P2",w,"7.5"],["stocks","384LDV_DMSO","P24","P2",w,"7.5"]]
    for w in singles_b:
        rows += [["stocks","384LDV_DMSO",sb,"P2",w,"7.5"],["stocks","384LDV_DMSO","P24","P2",w,"7.5"]]
    rows.append(["stocks","384LDV_DMSO","P24","P2",vehicle,"15"])
Path('/work/round2_picklist.csv').write_text(header+'\n'.join(','.join(r) for r in rows)+'\n')
