"""Build immutable synthetic rehearsals and the two reviewed production entries."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import build


def build_family(destination, source_manifest):
    destination = Path(destination)
    manifest = json.loads(Path(source_manifest).read_text("utf8"))
    if (manifest.get("constructed_only") is not True or manifest.get("private_source_reads") != 0
            or manifest.get("people") != 576 or set(manifest["sources"]) != {"M2"}):
        raise ValueError("Expected the sealed 576-person artificial-source manifest")
    if set(manifest["sources"]["M2"]) != {"survey", "diary"}:
        raise ValueError("Both constructed tables are required")
    for item in manifest["sources"]["M2"].values():
        name = item["filename"]
        if Path(name).name != name or len(item["sha256"]) != 64 or not 0 < item["bytes"] < 32000000:
            raise ValueError("Invalid constructed source identity")
        path = Path(source_manifest).parent/name
        if path.stat().st_size != item["bytes"] or sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Constructed table differs from its frozen edition")
    record = build.build(destination)
    modules = build.modules()
    worlds = build.ORIGINAL/"statcore-v2/mi_fixture_worlds_v1.py"
    modules["mi_fixture_worlds_v1"] = worlds.read_text("utf8")
    for name in ("joined_fixture", "daily_fixture", "family_rehearsal"):
        modules[name] = (build.HERE/(name+".py")).read_text("utf8")
    options = {"family-inside-rehearsal":True, "family-mounted-rehearsal":False}
    for name, inside in options.items():
        suffix = "from family_rehearsal import run\nraise SystemExit(run(" + repr(manifest["sources"]) + ", " + repr(inside) + "))\n"
        payload = build.single_file(modules, suffix)
        directory = destination/name
        directory.mkdir()
        (directory/"run.py").write_bytes(payload)
        record["jobs"][name] = sha256(payload).hexdigest()
    record["family_fixture_manifest_sha256"] = sha256(Path(source_manifest).read_bytes()).hexdigest()
    record["amendment_bf_sha256"] = sha256((build.REPO/"docs/design/stage-15/week6/D5_ARGUMENT_RESOLUTION_BF.md").read_bytes()).hexdigest()
    record["rehearsal_modules"] = {name:sha256(value.encode()).hexdigest() for name,value in modules.items()}
    (destination/"MANIFEST.json").write_text(json.dumps(record, indent=2)+"\n", "utf8")
    return record


if __name__ == "__main__":
    print(json.dumps(build_family(sys.argv[1],sys.argv[2])["jobs"],sort_keys=True))
