from pathlib import Path

header = 'Source Plate Name,Source Plate Type,Source Well,Destination Plate Name,Destination Well,Transfer Volume\n'
pairs = [
    (["A1","A3","A5","A7"],["A8","A9","A10","A12"]),
    (["A1","A3","A5","A7"],["A15","A17","A19","A21"]),
    (["A8","A9","A10","A12"],["A22","A23","A24","B2"]),
    (["B5","B6","B7","B9"],["B12","B13","B14","B16"]),
    (["B19","B20","B21","B23"],["A8","A9","A10","A12"]),
    (["B5","B6","B7","B9"],["A15","A17","A19","A21"]),
]
rows = []
def dest_well(n):
    return f"{'A' if n <= 48 else 'B'}{n if n <= 48 else n-48}"

for i, (a_sources, b_sources) in enumerate(pairs):
    base = i * 16
    combos = [dest_well(base+j+1) for j in range(4)]
    singles_a = [dest_well(base+j+5) for j in range(4)]
    singles_b = [dest_well(base+j+9) for j in range(4)]
    vehicle = dest_well(base+13)
    blank = dest_well(base+14)
    for well, sa, sb in zip(combos, a_sources, b_sources):
        rows += [["stocks","384LDV_DMSO",sa,"P1",well,"7.5"],
                 ["stocks","384LDV_DMSO",sb,"P1",well,"7.5"]]
    for well, sa in zip(singles_a, a_sources):
        rows += [["stocks","384LDV_DMSO",sa,"P1",well,"7.5"],
                 ["stocks","384LDV_DMSO","P24","P1",well,"7.5"]]
    for well, sb in zip(singles_b, b_sources):
        rows += [["stocks","384LDV_DMSO",sb,"P1",well,"7.5"],
                 ["stocks","384LDV_DMSO","P24","P1",well,"7.5"]]
    rows.append(["stocks","384LDV_DMSO","P24","P1",vehicle,"15"])
Path('/work/round1_picklist.csv').write_text(header + '\n'.join(','.join(r) for r in rows) + '\n')
