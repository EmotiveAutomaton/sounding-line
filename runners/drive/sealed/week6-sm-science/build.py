"""Build reproducible, self-contained jobs from the reviewed code-only evidence."""
from hashlib import sha256
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ORIGINAL = REPO / ".agent-state/drive-20261115/full-week-extension/mi"
WRAPPER = ORIGINAL / "sealed-wrapper-mi4-nullfix-v4"
QUALIFIED = {
    "mi_source_contract_v1", "mi_source_bridge_v1", "mi_stats_v1", "mi_reference_v1",
    "mi4_source_bridge_v1", "mi4_stats_v1", "mi4_reference_v1", "sealed_io_v1",
    "analysis_v1", "independent_v1", "aggregate_register_v1",
}
LOCAL = ("joined_source", "table_support", "panels", "family_draws", "engine", "science_entry")


def modules():
    sources = {}
    for row in json.loads((WRAPPER / "CODE_PINS.json").read_text("utf8"))["pins"]:
        path = ORIGINAL / row["path"]
        if path.stem not in QUALIFIED:
            continue
        data = path.read_bytes()
        if sha256(data).hexdigest() != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError("reviewed science source differs")
        sources[path.stem] = data.decode("utf8")
    if set(sources) != QUALIFIED:
        raise ValueError("reviewed science module missing")
    for name in LOCAL:
        sources[name] = (HERE / (name + ".py")).read_text("utf8")
    sources["week6_sealed_support_v1"] = (
        REPO / "runners/drive/cards/week6_sealed_support_v1.py"
    ).read_text("utf8")
    return sources


def single_file(sources, suffix):
    # Preserve the transparent originals in the evidence tree and bind every
    # embedded byte in MANIFEST.json. Imports may only use our fixed module names.
    boot = """import importlib,os,sys,tempfile
from pathlib import Path
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='2'
os.environ['CUDA_VISIBLE_DEVICES']=''
sys.dont_write_bytecode=True
"""
    boot += "SOURCES = " + repr(sources) + "\n"
    boot += """_code=tempfile.TemporaryDirectory(prefix='sm-code-')
_codepath=Path(_code.name)
for _name,_source in SOURCES.items():
    (_codepath/(_name+'.py')).write_bytes(_source.encode('utf8'))
sys.path.insert(0,str(_codepath))
_trusted_path=list(sys.path)
for _name in ('mi_source_contract_v1','mi_stats_v1','mi_reference_v1','mi_source_bridge_v1',
              'mi4_stats_v1','mi4_reference_v1','mi4_source_bridge_v1','sealed_io_v1',
              'independent_v1','aggregate_register_v1','analysis_v1'):
    sys.path[:]=_trusted_path
    _module=importlib.import_module(_name)
    if Path(_module.__file__).resolve()!=(_codepath/(_name+'.py')).resolve():
        raise SystemExit(14)
sys.path[:]=_trusted_path
"""
    text = boot + suffix
    compile(text, "<sealed-science>", "exec")
    return text.encode("utf8")


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    registry = json.loads((HERE / "source_map.json").read_text("utf8"))
    sources = modules()
    science = single_file(sources, "from science_entry import main\nraise SystemExit(main(" +
                          repr(registry) + "))\n")
    repeat = single_file(sources, "from science_entry import main\nraise SystemExit(main(" +
                         repr(registry) + ", 'M3'))\n")
    fixture_sources = dict(sources)
    fixture_file = ORIGINAL / "statcore-v2/mi_fixture_worlds_v1.py"
    fixture_sources["mi_fixture_worlds_v1"] = fixture_file.read_text("utf8")
    fixture_sources["joined_fixture"] = (HERE / "joined_fixture.py").read_text("utf8")
    rehearsal = single_file(fixture_sources, "from joined_fixture import rehearsal_main\n" +
                            "raise SystemExit(rehearsal_main(" + repr(registry) + "))\n")
    fixture_map = json.loads((HERE / "fixture_source_map.json").read_text("utf8"))
    scratch = single_file(fixture_sources, "from joined_fixture import mounted_rehearsal\nraise SystemExit(mounted_rehearsal(" +
                          repr(fixture_map) + "))\n")
    jobs = {}
    for name, payload in (("midus-m2-joined", science), ("midus-m2m3-joined", repeat),
                          ("rehearsal", rehearsal), ("scratch-rehearsal", scratch)):
        job = destination / name
        job.mkdir()
        (job / "run.py").write_bytes(payload)
        jobs[name] = sha256(payload).hexdigest()
    manifest = {
        "scope": "SM1 on wave two. SM2 uses both waves in the combined mount for eligibility and family linkage.",
        "jobs": jobs,
        "modules": {name: sha256(value.encode("utf8")).hexdigest()
                    for name, value in sorted(fixture_sources.items())},
        "source_map_sha256": sha256((HERE / "source_map.json").read_bytes()).hexdigest(),
        "constructed_source_map_sha256": sha256((HERE / "fixture_source_map.json").read_bytes()).hexdigest(),
        "science_draws": 2000, "numerical_threads": 2, "max_sealed_seconds": 21600,
        "max_private_read_bytes": 2_000_000_000,
    }
    (destination / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1])))
