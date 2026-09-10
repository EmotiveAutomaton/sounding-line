"""Consume an exact-package precision decision for an actually executed reader.

DESIGN CHECK: I03/X02/X06/X07/X12; LESSONS 3--5, CONTROLS 6.
NULL: missing, changed or failed calibration cannot become acceptance through file
presence or a different model identity. ALTERNATIVE: all saved fixture calls and
their live judgment reconstruct for the target's exact scoring package. This is
numerical instrument acceptance, not competence or generation-precision passage.
"""
import argparse
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.neural_operations import validate_complete
from runners.stage9.package_calibration import checked_calibration
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.training_jobs import cell_identity


def context(directory,calibration,target,scope,selected_calibrations=None,*,cell,source=None):
    """Reconstruct the same decision without writing or invoking a reader.

    Inspection supplies the original queue's source inventory. Its projection
    preserves this dispatcher's original source scope, including older queues.
    """
    directory,target=map(inside,(directory,target))
    prefix='calibration-check-pilots' if scope=='pilot' else 'scientific-calibration-check'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):
        raise ValueError('calibration consumer scope differs')
    ti=read(target/'IDENTITY.json');validate_complete(target,ti)
    if ti['scope']!=scope:raise ValueError('calibration target has a different data role')
    selection_provenance=None
    if selected_calibrations is not None:
        if calibration is not None:raise ValueError('selected calibration cannot also name a fixed calibration path')
        from runners.stage9.selected_recipe import calibration_path
        calibration,selection_provenance=calibration_path(selected_calibrations,ti,scope)
    elif calibration is None:raise ValueError('calibration consumer requires an actual calibration path')
    calibration=inside(calibration)
    package=read(target/'PACKAGE.json')
    decision=checked_calibration(calibration,package)
    if source is None:
        source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
            REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    else:
        files={p:sha for p,sha in source['files'].items() if p.startswith(
            ('runners/stage9/','runners/stage7/','runners/stage8/','soundingline/')) or p in
            {'runners/__init__.py','runners/readout_repair.py','runners/s3_lib.py','runners/s4_lib.py','runners/s5_lib.py'}}
        source={'files':files,'sha256':digest(files)}
    identity={'cell_identity':cell,'operation':'actual-package-calibration-consumer-v1','scope':scope,
        'source':source,'target':str(target),'calibration':str(calibration),
        'target_complete_sha256':file_hash(target/'COMPLETE.json'),
        'calibration_complete_sha256':file_hash(calibration/'COMPLETE.json'),'package':package}
    if selection_provenance is not None:identity['selected_calibration']=selection_provenance
    return identity,decision


def run(directory,calibration,target,scope,selected_calibrations=None):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity()
    identity,decision=context(directory,calibration,target,scope,selected_calibrations,cell=cell)
    directory=inside(directory);source=identity['source']
    with writer(directory):
        Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed calibration consumption changed')
            return done
        freeze(directory/'DECISION.json',decision);verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
            'instrument_accepted':decision['instrument_accepted'],'scientific_admission':False,
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/'IDENTITY.json',directory/'DECISION.json'])}
        freeze(directory/'COMPLETE.json',done);return done


def argument_parser():
    p=argparse.ArgumentParser()
    for name in ('output','target'):p.add_argument('--'+name,type=Path,required=True)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--calibration',type=Path);group.add_argument('--selected-calibrations',type=Path)
    p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,a.calibration,a.target,a.scope,a.selected_calibrations)
