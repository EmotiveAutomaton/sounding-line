"""Build reproducible, self-contained SC2 entries for the installed sealed runner."""
import base64
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[3]
HERE = Path("runners/drive/sealed")
MODULES = (Path("runners/drive/cards/week6_sealed_support_v1.py"),
           *(HERE / ("week6_sc" + name + "_v1.py") for name in
             ("1_counts", "2_source", "2_reader", "2_status", "2_model", "2_job")))
CONSTRUCTED = HERE / "week6_sc2_constructed_v1.py"


def entry(rehearsal=False):
    sources = {p.as_posix(): (ROOT / p).read_bytes() for p in MODULES}
    if rehearsal:
        sources[CONSTRUCTED.as_posix()] = (ROOT / CONSTRUCTED).read_bytes()
    for folder in ("runners", "runners/drive", "runners/drive/cards", "runners/drive/sealed"):
        sources[folder + "/__init__.py"] = b""
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, payload in sorted(sources.items()):
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
    packed = base64.b85encode(buffer.getvalue()).decode("ascii")
    if rehearsal:
        call = "from runners.drive.sealed.week6_sc2_constructed_v1 import known_answer as execute"
    else:
        call = "from runners.drive.sealed.week6_sc2_job_v1 import main as execute"
    lines = [
        '"""Frozen Sounding Line SC2 sealed entry."""',
        "import base64, os, sys, tempfile",
        "from pathlib import Path",
        "for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):",
        "    os.environ[key] = '2'",
        "os.environ['CUDA_VISIBLE_DEVICES'] = ''",
        "with tempfile.TemporaryDirectory(prefix='sc2-code-') as temp:",
        "    package = Path(temp) / 'reviewed.zip'",
        "    package.write_bytes(base64.b85decode(" + repr(packed) + "))",
        "    sys.path.insert(0, str(package))",
        "    " + call,
        "    raise SystemExit(execute())",
    ]
    return ("\n".join(lines) + "\n").encode("utf8")


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    jobs = {}
    for name, rehearsal in (("constructed", True), ("matched", False)):
        payload = entry(rehearsal)
        folder = destination / name
        folder.mkdir(exist_ok=True)
        output = folder / "run.py"
        if output.exists():
            if output.read_bytes() != payload:
                raise ValueError("Existing sealed entry differs")
        else:
            with output.open("xb") as stream:
                stream.write(payload)
        jobs[name] = hashlib.sha256(payload).hexdigest()
    return jobs


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Supply a new output directory")
    print(json.dumps(build(sys.argv[1]), sort_keys=True))
