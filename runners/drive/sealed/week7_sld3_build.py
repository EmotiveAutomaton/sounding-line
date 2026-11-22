"""Make the sealed entry from the exact TRX1 function and reviewed MIDUS reader."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE/'week6-sm-science'))
import build


def modules():
    sources=build.modules()
    cards=REPO/'runners/drive/cards'
    trait=(cards/'week7_trait_v1.py').read_text('utf8')
    body,=[x for x in ast.parse(trait).body if isinstance(x,ast.FunctionDef) and x.name=='effect']
    sources['frozen_trait']='import numpy as np\nimport week6_person_slopes_v1 as ref\n'+ast.get_source_segment(trait,body)+'\n'
    sources['week6_person_slopes_v1']=(cards/'week6_person_slopes_v1.py').read_text('utf8')
    sources['independent_release']=(HERE/'week6-sm-science/independent_release.py').read_text('utf8')
    sources['week7_sld3']=(HERE/'week7_sld3.py').read_text('utf8')
    return sources


def package(destination,fixture_map=None):
    destination.mkdir(parents=True,exist_ok=False)
    source_map=json.loads((HERE/'week6-sm-science/source_map.json').read_text('utf8'))
    source_map={'M2':source_map['M2']}
    if fixture_map is not None:
        if set(fixture_map)!={'M2'} or set(fixture_map['M2'])!={'diary','survey'}:
            raise ValueError('two reviewed wave-two fixture tables required')
        source_map=fixture_map
    sources=modules()
    call=('run(Path("/data"),Path("/out"),'+repr(source_map)+')' if fixture_map is None else
          'run(Path(sys.argv[1]),Path(sys.argv[2]),'+repr(source_map)+',draws=6)')
    entry=build.single_file(sources,
        'from week7_sld3 import run\nfrom week6_sealed_support_v1 import SealedFailure\n'
        +'try:\n    '+call+'\n'
        +'except SealedFailure as exc:\n    raise SystemExit(exc.code) from None\n')
    (destination/'run.py').write_bytes(entry)
    manifest=dict(entry_sha256=sha256(entry).hexdigest(),module_hashes={
        name:sha256(code.encode()).hexdigest() for name,code in sorted(sources.items())},
        source_map=source_map,draws=2000 if fixture_map is None else 6,
        constructed_only=fixture_map is not None,numerical_threads=2)
    (destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')


if __name__=='__main__':
    package(Path(sys.argv[1]))
