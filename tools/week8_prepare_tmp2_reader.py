"""Prepare the original TMP2 reader and release it only after its fallback boundary."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_tmp2 as study
from runners.stage14.common import filehash,freeze,read
from tools.week8_sealed import STATE

EARLIEST=datetime(2026,11,28,2,50,tzinfo=timezone.utc)
CAP=15400


def prepare(release=False, tp72_absent=False):
    binding, payload, pins=study.reviewed()
    unit=study.UNIT
    entry=STATE/'sealed'/unit/'run.py'
    entry.parent.mkdir(parents=True,exist_ok=True)
    program=study.package.package(study.STUDY,study.MODULES,dict(files=binding['archives'],payload=payload,real_image=True),CAP)
    if entry.exists():
        if entry.read_bytes()!=program:raise ValueError('Existing entry differs')
    else:
        with entry.open('xb') as out:out.write(program)
    if not release:
        print('Prepared fallback entry',filehash(entry))
        return
    when=datetime.now(timezone.utc)
    if not EARLIEST<=when<study.gear.FREEZE or not tp72_absent:
        raise ValueError('Fallback requires the twelve-hour boundary and a fresh check of the engine delivery')
    directory=study.gear.ROOT/study.FIXTURE
    complete=read(directory/'COMPLETE.json')
    evidence=directory/'REHEARSAL.json'
    reviewed=STATE/'reviews'/(study.FIXTURE+'.json')
    if (not complete['verified'] or complete['review_sha256']!=filehash(reviewed)
            or complete['results'].get(evidence.name)!=filehash(evidence)
            or not read(evidence)['independent_projection_and_reader_replay']
            or not read(evidence)['installed_gate_passed']
            or read(reviewed)['fixture']['compiled_entry_sha256']!=filehash(entry)):
        raise ValueError('Complete independent rehearsal required for these bytes')
    # Record the alias and mapped headers for this single combined mount.
    rec=STATE/'TMP2_TP58_DJ_BINDING.json'
    obj=dict(binding,mount=study.ALIAS,combined_source_receipt_sha256=study.RECEIPT_DIGEST)
    if rec.exists() and read(rec)!=obj:raise ValueError('Existing combined binding differs')
    if not rec.exists():freeze(rec,obj)
    pins.extend([reviewed,directory/'COMPLETE.json',evidence,entry,rec,Path(study.gear.__file__),
                 study.gear.AUTHORITY,Path(__file__)])
    this_review=dict(unit=unit,card='TMP2',source=study.ALIAS,cap=CAP,tables=study.TABLES,
                     not_before=EARLIEST.isoformat(),fixture_gate_passed=True,fixture_sha256=filehash(evidence),
                     receipt_sha256=filehash(rec),provider_binding_sha256=filehash(study.MAPPING),
                     fallback_reason='Verified TP72 delivery absent at the twelve-hour review',
                     pins={str(p):filehash(p) for p in pins})
    target=STATE/'reviews'/(unit+'.json')
    if target.exists():
        if read(target)!=this_review:raise ValueError('Different research review already present')
    else:
        freeze(target,this_review)
    print('Fallback admitted',filehash(target))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--release-fallback',action='store_true')
    parser.add_argument('--tp72-absent',action='store_true',help='Operating owner has just checked the producer and archive deliveries')
    args=parser.parse_args()
    prepare(args.release_fallback,args.tp72_absent)
