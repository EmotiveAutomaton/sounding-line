"""Build sealed jobs from exact reviewed modules; no source read or invocation.

DESIGN CHECK: LESSONS 2-5. Generated jobs bind all module and mapping bytes.
Both real aliases are joined folders; a fresh destination prevents replacement.
"""
import hashlib
import json
from pathlib import Path
import sys


def build(destination):
    here = Path(__file__).resolve().parent
    root = here.parents[3]
    mapping_path = root/'docs/design/stage-15/week6/SM0_JOINED_MAPPINGS_V1.json'
    mappings = json.loads(mapping_path.read_text('utf8'))['mappings']
    assert [m['source_alias'] for m in mappings] == ['midus-m2-joined','midus-m3-joined']
    names = ['week6_sealed_support_v1','week6_sm0_probe_v1','week6_sm0_probe_v2','week6_sm0_probe_v3']
    sources = {'runners.drive.cards.'+n:(root/'runners/drive/cards'/(n+'.py')).read_text('utf8') for n in names}
    prefix = "import os, sys, types\n"
    prefix += "for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='2'\nos.environ['CUDA_VISIBLE_DEVICES']=''\n"
    prefix += 'SOURCES = '+repr(sources)+'\nMAPPINGS = '+repr(mappings)+'\n'
    prefix += "for name in ('runners','runners.drive','runners.drive.cards'):\n m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m\n"
    prefix += "for name,source in SOURCES.items():\n m=types.ModuleType(name);sys.modules[name]=m;exec(compile(source,'<reviewed-probe>','exec'),m.__dict__)\n"
    prefix += "P=sys.modules['runners.drive.cards.week6_sm0_probe_v3']\nS=sys.modules['runners.drive.cards.week6_sealed_support_v1']\n"
    prefix += "if os.name=='posix':\n import resource,signal\n resource.setrlimit(resource.RLIMIT_CPU,(600,600));signal.alarm(600)\n"
    jobs = {'rehearsal':prefix+(here/'fixture.py').read_text('utf8')}
    for i, mapping in enumerate(mappings):
        jobs[mapping['source_alias']] = prefix+f"raise SystemExit(P.exit_code('/data','/out',MAPPINGS[{i}]))\n"
    destination = Path(destination); destination.mkdir(parents=True,exist_ok=False)
    hashes = {}
    for name, text in jobs.items():
        compile(text,'<sealed-joined>','exec')
        folder=destination/name;folder.mkdir();(folder/'run.py').write_bytes(text.encode('utf8'))
        hashes[name]=hashlib.sha256(text.encode('utf8')).hexdigest()
    manifest=dict(mapping_sha256=hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
        modules={n:hashlib.sha256(s.encode('utf8')).hexdigest() for n,s in sources.items()},
        fixture_sha256=hashlib.sha256((here/'fixture.py').read_bytes()).hexdigest(),
        jobs=hashes,expected_cases=10,max_cpu_seconds=600,max_wall_seconds=600,
        numerical_threads=2,max_private_read_bytes=2_000_000_000,scientific_admission=False)
    (destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps(manifest))


if __name__=='__main__': build(sys.argv[1])
