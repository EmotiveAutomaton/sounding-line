"""Create the same isolated CAD2 entry for the projected-source fixture and Spark."""
import base64
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from runners.drive.sealed.week7_bounded_entry import bounded
from runners.theory_days.launch import REPO, closure


PINS = {
    'cad2-aws2020.zip': (133892073, '10a66e11820eb5cb301695baf5e72643da3216296ba1eff2b19cbcd91ff62416'),
    'MANIFEST.json': (1374301, 'f1b2d6ce36a4ed199f35b9f6d1b7db673c0cd189ecf138cbff4c001702548864'),
}
MODULE = 'runners.drive.sealed.week7_cad2_original'


def package(folder, *, fixture=None):
    sources = {p.relative_to(REPO).as_posix(): p.read_bytes() for p in closure([MODULE])}
    files = {name: sha256(data).hexdigest() for name, data in sources.items()}
    for name in list(sources):
        for parent in Path(name).parents:
            if parent != Path('.'):
                sources.setdefault((parent/'__init__.py').as_posix(), b'')
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w') as archive:
        for name, data in sorted(sources.items()):
            archive.writestr(ZipInfo(name), data, compress_type=ZIP_DEFLATED)
    packed = base64.b85encode(buffer.getvalue()).decode('ascii')
    pins, calls, draws = (PINS, 1656, 2000) if fixture is None else fixture
    source_setup = """mount, out = Path('/data'), Path('/out')
options = [s.split()[5].split(',') for s in Path('/proc/self/mountinfo').read_text().splitlines() if s.split()[4]=='/data']
if len(options) != 1 or 'ro' not in options[0]: raise SystemExit(13)
""" if fixture is None else "mount, out = map(Path, sys.argv[1:])"
    script = f"""import base64, gc, io, os, sys, tempfile, zipfile
from pathlib import Path
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '2'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
{source_setup}
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    with zipfile.ZipFile(io.BytesIO(base64.b85decode({packed!r}))) as archive:
        archive.extractall(root)
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True
    from runners.drive.sealed.week7_cad2_original import run, SealedFailure
    results = []
    for attempt in ('first','replay'):
        dest = root/attempt
        dest.mkdir()
        try:
            run(mount, dest, {pins!r}, {calls}, {draws})
        except SealedFailure as exc:
            raise SystemExit(exc.code) from None
        except (ValueError, KeyError, TypeError, IndexError, UnicodeError, zipfile.BadZipFile):
            raise SystemExit(11) from None
        results.append({{p.name:p.read_bytes() for p in dest.iterdir()}})
        gc.collect()
    if results[0] != results[1] or 'support.csv' not in results[0] or set(results[0])-{{'support.csv','timing.csv'}}:
        raise SystemExit(14)
    for name, data in results[0].items():
        (out/name).write_bytes(data)
"""
    entry = bounded(script.encode())
    compile(entry, 'cad2/run.py', 'exec')
    folder.mkdir()
    (folder/'run.py').write_bytes(entry)
    (folder/'MANIFEST.json').write_text(json.dumps(dict(sources=files, draws=draws, calls=calls,
        fixture=fixture is not None, entry=sha256(entry).hexdigest(), pins=pins), indent=2)+'\n','utf8')
