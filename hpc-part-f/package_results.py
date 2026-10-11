from pathlib import Path
import hashlib, json, zipfile, difflib
root = Path.cwd()
assert len((root/'raw.csv').read_text().splitlines())==121
assert (root/'summary.csv').is_file()
patch=[]
for name in ['random_forest.cpp','decision_tree.cpp']:
    old=(root.parent/'src-openmp'/name).read_text().splitlines(True)
    new=(root/'src-openmp'/name).read_text().splitlines(True)
    patch.extend(difflib.unified_diff(old,new,fromfile='a/src-openmp/'+name,tofile='b/src-openmp/'+name))
(root/'source-corrections.patch').write_text(''.join(patch))
files=[p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS.json']
sums={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(root/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2))
archive=root.parent/'hpc-part-f-evidence.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files+[root/'SHA256SUMS.json']:
        z.write(p,'hpc-part-f/'+p.relative_to(root).as_posix())
    z.write(root.parent/'data/sonar.all-data.numerical.csv','data/sonar.all-data.numerical.csv')
    z.write(root.parent/'LICENSE','LICENSE')
print('ARCHIVE',archive.name,'SHA256',hashlib.sha256(archive.read_bytes()).hexdigest())
print('MEASUREMENT FILES AND SOURCE PACKAGED')

