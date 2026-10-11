from pathlib import Path
import csv, json, os, random, subprocess, time, math, statistics, hashlib
root = Path.cwd()
env = dict(os.environ, OMP_DYNAMIC='FALSE', OMP_MAX_ACTIVE_LEVELS='1', OMP_PROC_BIND='FALSE')
def measure(trees, threads, label):
    e = dict(env, OMP_NUM_THREADS=str(threads))
    t = time.time()
    p = subprocess.run(['./benchmark', str(trees), str(threads)], env=e, text=True, capture_output=True, timeout=900)
    (root / 'logs').mkdir(exist_ok=True)
    (root / 'logs' / (label+'.txt')).write_text(p.stdout+p.stderr)
    if p.returncode: raise RuntimeError((label, p.returncode, p.stdout, p.stderr))
    lines = [x.split() for x in p.stdout.splitlines() if x.startswith('RESULT ')]
    assert len(lines)==1, p.stdout
    _, n, requested, actual, elapsed, checksum, acc = lines[0]
    assert int(n)==trees and int(requested)==threads and int(actual)==threads
    row = dict(trees=trees, threads=threads, actual_threads=int(actual), seconds=float(elapsed), checksum=checksum, test_accuracy=float(acc), started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(t)))
    print(label, row, flush=True)
    return row
info = dict(codespace=os.environ.get('CODESPACE_NAME'), affinity=sorted(os.sched_getaffinity(0)), cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(), compiler=subprocess.check_output(['g++','--version'],text=True), lscpu=subprocess.check_output(['lscpu'],text=True), uname=subprocess.check_output(['uname','-a'],text=True), commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(), flags='-std=c++14 -O0 -fopenmp', timing='RandomForest constructor including fit, excluding CSV loading, splitting and prediction', seeds=dict(split=1337,forest=69), omp=dict(dynamic=False,max_active_levels=1,proc_bind=False), dataset_sha256=hashlib.sha256(Path('../data/sonar.all-data.numerical.csv').read_bytes()).hexdigest())
Path('environment.json').write_text(json.dumps(info,indent=2))
checks = [measure(20,p,'correctness_'+str(p)) for p in [1,2,3,4]]
assert len({x['checksum'] for x in checks})==1, 'Predictions differ by thread count'
Path('correctness.json').write_text(json.dumps(checks,indent=2))
pilot = measure(100,1,'pilot_100')
base = max(100,math.ceil(100*23/pilot['seconds']/10)*10)
calibration = []
while True:
    row = measure(base,1,'calibrate_'+str(base))
    calibration.append(row)
    if row['seconds']>=22: break
    base = math.ceil(base*23/row['seconds']/10)*10
Path('calibration.json').write_text(json.dumps(dict(base_trees=base,pilot=pilot,runs=calibration),indent=2))
jobs = [(r,w,p) for r in range(1,11) for w in [1,2,4] for p in [1,2,3,4]]
random.Random(2026).shuffle(jobs)
fields = ['run','workload','trees','threads','actual_threads','seconds','checksum','test_accuracy','started_utc']
rows=[]
with open('raw.csv','w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); f.flush()
    for index,(r,w,p) in enumerate(jobs,1):
        row=measure(base*w,p,f'run_{r}_w{w}_p{p}')
        row.update(run=r,workload=w)
        writer.writerow(row); f.flush(); os.fsync(f.fileno()); rows.append(row)
        for other in rows:
            if other['workload']==w: assert other['checksum']==row['checksum'], 'Predictions differ'
        print(f'PROGRESS {index}/120',flush=True)
groups={}
for w in [1,2,4]:
    for p in [1,2,3,4]:
        values=[x['seconds'] for x in rows if x['workload']==w and x['threads']==p]
        assert len(values)==10
        groups[w,p]=dict(workload=w,trees=base*w,threads=p,runs=10,mean_seconds=statistics.mean(values),stdev_seconds=statistics.stdev(values),min_seconds=min(values),max_seconds=max(values))
with open('summary.csv','w',newline='') as f:
    fields2=list(next(iter(groups.values())))+['speedup','efficiency']
    writer=csv.DictWriter(f,fieldnames=fields2);writer.writeheader()
    for (w,p),row in groups.items():
        row['speedup']=groups[w,1]['mean_seconds']/row['mean_seconds'];row['efficiency']=row['speedup']/p;writer.writerow(row)
print('COMPLETE',json.dumps(list(groups.values())),flush=True)

