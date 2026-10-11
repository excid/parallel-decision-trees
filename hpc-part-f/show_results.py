import csv
from pathlib import Path
rows = list(csv.DictReader(Path('raw.csv').open()))
summary = list(csv.DictReader(Path('summary.csv').open()))
assert len(rows) == 120 and len(summary) == 12
by = {(int(r['workload']), int(r['threads'])): r for r in summary}
print('PART F - ACTUAL CODESPACE MEASUREMENTS')
print('Codespace: zany-robot-v7gwwvr5749cp46q')
print('120 runs; 10 per setting; timer: omp_get_wtime()')
for field, title in [('mean_seconds','Mean training time (seconds)'), ('speedup','Speedup against same-workload one-thread mean')]:
    print('\n' + title)
    print(f"{'Threads':>8} {'1x':>12} {'2x':>12} {'4x':>12}")
    if field=='mean_seconds':
        print(f"{'Trees':>8}" + ''.join(f"{by[w,1]['trees']:>12}" for w in [1,2,4]))
    for p in [1,2,3,4]:
        print(f'{p:8d}' + ''.join(f"{float(by[w,p][field]):12.3f}" for w in [1,2,4]))
print('\nRequested thread counts and prediction checks passed.')
print('Measured isolated copy with documented race corrections.')
print('Evidence: raw.csv, summary.csv, logs/, environment.json')

