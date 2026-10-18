"""Authenticate the externally pinned October18 canonical-selection audit.

This adapter executes only the reviewed, hash-locked read-only audit helper.
All prepared/canonical/foundation dependencies are authenticated by that helper;
P8 option identity and original raw-source hashes are separately joined here.
No prepared inserted text or logged selection index becomes a target.
"""
from pathlib import Path
import importlib.util

from .menus_io import sha256

READER_SHA256 = "b080b930ceecc3d83ff14b584157d22e1b3939c533db17cec0ce9eb9440e2fe5"
SESSION_SUFFIX = Path("results/phase_2_4_stage_15/raw/phase0-v1/prepared/SESSIONS.json")


def load(inputs):
    helper=Path(inputs["selection_reader"]).resolve()
    if sha256(helper)!=READER_SHA256:
        raise ValueError("canonical audit reader source changed")
    session=Path(inputs["sessions"]).resolve()
    repository=session.parents[len(SESSION_SUFFIX.parts)-1]
    if repository/SESSION_SUFFIX != session:
        raise ValueError("canonical audit prepared-source layout differs")
    spec=importlib.util.spec_from_file_location("soundingline_frozen_selection_audit",helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    complete=Path(inputs["selection_complete"]).resolve()
    return module.load_audit(repository,complete.parent,sha256(complete))


def join(audit,row,options):
    proof=audit.join(row)
    ordered=sorted(options,key=lambda p:p["position"])
    if [p["position"] for p in ordered] != list(range(len(row["menu"]))):
        raise ValueError("canonical/P8 positional coverage differs")
    if [p["suggestion_index"] for p in ordered] != proof["canonical_option_ids"]:
        raise ValueError("canonical/P8 original option identity differs")
    if any(p["source_sha256"]!=proof["raw_source_sha256"] for p in ordered):
        raise ValueError("canonical/P8 raw-source identity differs")
    accepted=row["handling"] in ("accept","edit")
    actual=proof["canonical_positions"]
    if accepted and (len(actual)!=1 or not proof["verified_insertion"] or not proof["canonical_usable"]):
        raise ValueError("canonical selected option is not uniquely verified")
    if not accepted and actual:
        raise ValueError("unselected decision has a canonical selected option")
    return proof, actual[0] if accepted else None
