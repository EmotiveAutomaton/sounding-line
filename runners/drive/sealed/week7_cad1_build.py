"""Build the self-contained CAD1 sealed job using the pinned SC2 dependencies."""
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import base64
import sys

from runners.drive.sealed.week6_sc2_build_v1 import ROOT


def package(destination,fixture_pins=None):
    files=('runners/drive/sealed/week7_cad1.py',
           'runners/drive/sealed/week6_sc1_counts_v1.py',
           'runners/drive/sealed/week6_sc2_source_v1.py',
           'runners/drive/cards/week6_sealed_support_v1.py')
    source={name:(ROOT/name).read_bytes() for name in files}
    for path in ('runners','runners/drive','runners/drive/cards','runners/drive/sealed'):
        source[path+'/__init__.py']=b''
    archive=io.BytesIO()
    with ZipFile(archive,'w') as out:
        for name,content in sorted(source.items()):
            out.writestr(ZipInfo(name),content,compress_type=ZIP_DEFLATED)
    packed=base64.b85encode(archive.getvalue()).decode('ascii')
    script='''import base64, os, sys, tempfile
from pathlib import Path
for key in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[key]="2"
os.environ["CUDA_VISIBLE_DEVICES"]=""
with tempfile.TemporaryDirectory() as temp:
    code=Path(temp)/"reviewed.zip"
    code.write_bytes(base64.b85decode(PACKED))
    sys.path.insert(0,str(code))
    from runners.drive.sealed.week7_cad1 import run, Unavailable, SealedFailure
    try:
        run(Path("/data"),Path("/out"))
    except Unavailable as err:
        raise SystemExit(err.args[0]) from None
    except SealedFailure as err:
        raise SystemExit(err.code) from None
'''.replace('b85decode(PACKED)','b85decode('+repr(packed)+')')
    if fixture_pins is not None:
        if set(fixture_pins)!={'survey','speech','clock'}:
            raise ValueError('three reviewed fixture tables required')
        script=script.replace('run(Path("/data"),Path("/out"))',
                              'run(Path(sys.argv[1]),Path(sys.argv[2]),'+repr(fixture_pins)+',draws=6)')
    compile(script,'CAD1/run.py','exec')
    destination.mkdir(parents=True,exist_ok=False)
    entry=script.encode('utf8')
    (destination/'run.py').write_bytes(entry)
    (destination/'MANIFEST.json').write_text(json.dumps(dict(
        entry_sha256=sha256(entry).hexdigest(),
        sources={name:sha256(source[name]).hexdigest() for name in files},
        mood_before='pre_affect',outcome='own speech rate',enjoyment='how_enjoyable',
        draws=2000 if fixture_pins is None else 6,constructed_only=fixture_pins is not None,
        numerical_threads=2),indent=2)+'\n','utf8')


if __name__=='__main__':
    package(Path(sys.argv[1]))
