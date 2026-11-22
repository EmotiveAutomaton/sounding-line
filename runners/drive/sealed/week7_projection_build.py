"""Package a constructed-only projection with its source identity and local gate."""
import base64
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from runners.theory_days.launch import REPO, closure


NAMES={'cad2':('words.json',),'lgh1':('sound.json',),'lgh2':('mood.csv',),
       'sld2':tuple(f'made_wave_{i}.csv' for i in (1,2,3))}


def package(card,fixture,destination,*,draws):
    if card not in NAMES or not 2<=draws<=2000:
        raise ValueError('unregistered rehearsal')
    fixture=Path(fixture)
    digests={name:sha256((fixture/name).read_bytes()).hexdigest() for name in NAMES[card]}
    module='runners.drive.sealed.week7_'+card
    sources={p.relative_to(REPO).as_posix():p.read_bytes() for p in closure([module])}
    for name in list(sources):
        parent=Path(name).parent
        while parent!=Path('.'):
            sources.setdefault((parent/'__init__.py').as_posix(),b'')
            parent=parent.parent
    buffer=io.BytesIO()
    with ZipFile(buffer,'w') as archive:
        for name,data in sorted(sources.items()):
            archive.writestr(ZipInfo(name),data,compress_type=ZIP_DEFLATED)
    packed=base64.b85encode(buffer.getvalue()).decode('ascii')
    call={
        'cad2':"study.run(json.loads((mount/'words.json').read_text('utf8')),out,draws)",
        'lgh1':"data=json.loads((mount/'sound.json').read_text('utf8')); study.evaluate(data['x'],data['meta'],out,draws=draws)",
        'lgh2':"study.run(pd.read_csv(mount/'mood.csv'),out,marked=True,draws=draws)",
        'sld2':"study.rehearse(mount,out,['item1','item2'],draws)",
    }[card]
    lines=['"""Synthetic projection rehearsal. Bound to these exact made inputs."""',
           'import base64, hashlib, importlib, io, json, os, sys, tempfile, zipfile','from pathlib import Path',
           'for k in ("OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"): os.environ[k]="2"',
           'os.environ["CUDA_VISIBLE_DEVICES"]=""','import pandas as pd',
           'mount=Path(sys.argv[1]) if len(sys.argv)==3 else Path("/data")',
           'out=Path(sys.argv[2]) if len(sys.argv)==3 else Path("/out")',
           'for name,digest in '+repr(digests)+'.items():',
           '    p=mount/name','    if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise SystemExit(11)',
           'draws='+str(draws),'with tempfile.TemporaryDirectory() as work:',
           '    with zipfile.ZipFile(io.BytesIO(base64.b85decode('+repr(packed)+'))) as code:',
           '        for name in '+repr(sorted(sources))+':',
           '            target=Path(work)/name','            target.parent.mkdir(parents=True,exist_ok=True)',
           '            target.write_bytes(code.read(name))',
           '    sys.dont_write_bytecode=True','    sys.path.insert(0,work)',
           '    study=importlib.import_module('+repr(module)+')','    '+call]
    payload=('\n'.join(lines)+'\n').encode()
    compile(payload,'run.py','exec')
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'run.py').write_bytes(payload)
    manifest=dict(card=card,constructed_only=True,input_sha256=digests,entry_sha256=sha256(payload).hexdigest(),
                  source_sha256={name:sha256(data).hexdigest() for name,data in sources.items()},
                  draws=draws)
    (destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')
