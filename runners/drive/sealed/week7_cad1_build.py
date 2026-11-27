"""Build the self-contained CAD1 sealed job using the pinned SC2 dependencies."""
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import base64
import sys

from runners.drive.sealed.week6_sc2_build_v1 import ROOT


def package(destination,fixture_pins=None,*,primary_only=False,attention_key=None,published_support=None):
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
    followup = attention_key is not None
    if followup != (published_support is not None) or (followup and primary_only):
        raise ValueError('Expanded follow-up requires the export key and both published counts')
    if followup:
        ranks=[v for v in attention_key.values() if v is not None]
        if (sorted(ranks)!=list(range(1,8)) or any(type(k) is not int for k in attention_key)
                or len(published_support)!=2 or any(type(n) is not int or n<11 for n in published_support)):
            raise ValueError('Invalid response mapping or prior cohort counts')
    if primary_only or followup:
        from runners.drive.sealed.week7_bounded_entry import bounded
        mount="Path(sys.argv[1])" if fixture_pins is not None else "Path('/data')"
        target="Path(sys.argv[2])" if fixture_pins is not None else "Path('/out')"
        binding="" if fixture_pins is not None else """
        options=[s.split()[5].split(',') for s in Path('/proc/self/mountinfo').read_text().splitlines() if s.split()[4]=='/data']
        if len(options)!=1 or 'ro' not in options[0]:raise SystemExit(13)
"""
        call=next(line for line in script.splitlines() if line.startswith('        run('))
        args=('pins='+repr(fixture_pins)+',draws=8,') if fixture_pins is not None else ''
        options='expanded=False,response_domains=domains'
        extra=''
        if followup:
            extra=f"domains.update(overall_affect=range(1,10),i_like_you=range(1,8),my_partner_paid_attention_to_me={tuple(attention_key)!r})"
            options=f"response_domains=domains,published_support={tuple(published_support)!r},attention_key={attention_key!r}"
        script=script.replace(call,binding+f"""
        domains={{key:range(1,10) for key in ('how_enjoyable','arousal','pre_affect')}}
        {extra}
        outputs=[]
        for repeat in range(2):
            dest=Path(temp)/str(repeat)
            dest.mkdir()
            run({mount},dest,{args}{options})
            outputs.append({{p.name:p.read_bytes() for p in dest.iterdir()}})
        if outputs[0]!=outputs[1] or 'support.csv' not in outputs[0] or set(outputs[0])-{{'pace.csv','support.csv'}}:
            raise SystemExit(14)
        for name,data in outputs[0].items():
            ({target}/name).write_bytes(data)
""")
        script=bounded(script.encode()).decode()
    compile(script,'CAD1/run.py','exec')
    destination.mkdir(parents=True,exist_ok=False)
    entry=script.encode('utf8')
    (destination/'run.py').write_bytes(entry)
    (destination/'MANIFEST.json').write_text(json.dumps(dict(
        entry_sha256=sha256(entry).hexdigest(),
        sources={name:sha256(source[name]).hexdigest() for name in files},
        mood_before='pre_affect',outcome='own speech rate',enjoyment='how_enjoyable',
        draws=2000 if fixture_pins is None else (8 if primary_only or followup else 6),constructed_only=fixture_pins is not None,
        primary_only=primary_only,
        numerical_threads=2),indent=2)+'\n','utf8')


if __name__=='__main__':
    package(Path(sys.argv[1]))
