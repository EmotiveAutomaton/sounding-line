"""Explicit training-only executable library and common comparator candidates.

DESIGN CHECK: M01/M02/C08/X01/X11; LESSONS 3--5. NULL: pilot allocation,
nontraining combinations, incomplete cohorts or a failed fit cannot become a
scientific model package. ALTERNATIVE: all declared numerical model candidates fit
only permitted training boundaries, with identities and optimization outcomes saved.
Bands: all declared fits complete, or refusal; development selection is separate.
This handler never evaluates held-out units and never opens a confirmation reserve.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import itertools
import os
from pathlib import Path
import time
import traceback

from .artifact_training import LAWS,RESIDUES,prepare
from .artifact_preparation import evidence
from .artifact_view import TYPES,action_id
from .choice_fit import fit as fit_choice
from .common import REPO,ROOT,closure,digest,freeze,read,write,distribution
from .mark_program import validate as validate_program
from .program_fit import fit_library
from .queue import inside,verify_sources,writer
from .recipes import POP,PURPOSES,sampled_world,parameter_partition

REGULARIZERS=(.01,.1)
ADAPTATION_STRENGTHS=(8.,16.,32.)


def validate_prepared(data,*,band,per_domain,view):
    receipt=data['receipt']
    if (receipt['records_sha256']!=digest(data['records']) or receipt['unit_ledger_sha256']!=digest(data['units']) or
        receipt['band']!=band or receipt['per_domain']!=per_domain or receipt['view']!=view or
        len(data['units'])!=96*per_domain or len({u['unit'] for u in data['units']})!=len(data['units'])):
        raise ValueError('prepared training allocation or content identity mismatch')
    rebuilt=[];cohorts=Counter()
    for unit in data['units']:
        world=sampled_world(unit['lineage'],'both')
        if (digest(world)!=unit['source_sha256'] or digest({'whole_training_world':world})!=unit['unit'] or
            parameter_partition(world)!='training' or unit['parameter_partition']!='training'):
            raise ValueError('training source world does not reconstruct in its permitted partition')
        names=world['state']['names'];events=world['trajectory']['steps']
        cohort=(names['law'],names['residue'],world['goal_name'],world['domain'])
        if list(cohort)!=unit['cohort']:
            raise ValueError('training cohort differs from actual source')
        cohorts[cohort]+=1
        targets=[(i,action_id(event)) for i,event in enumerate(events)]
        if world['trajectory']['stop_kind']=='hazard':targets.append((len(events),'stop'))
        for boundary,target in targets:
            rebuilt.append({'unit':unit['unit'],'evidence':evidence(world,events[:boundary],view),'target':target,
                            'maker_group':names['law']+'|'+names['residue'],'purpose_group':world['goal_name']})
    if rebuilt!=data['records']:
        raise ValueError('training inputs or targets differ from actual source reconstruction')
    if cohorts!={c:per_domain for c in itertools.product(LAWS,RESIDUES,PURPOSES,POP.DOMAINS)}:
        raise ValueError('declared training cohort balance is incomplete')
    return True


def validate_library(library,audit,records,training_units,*,minimum_units,expected_candidates=48):
    if (audit['training_records_sha256']!=digest(records) or audit['training_units_sha256']!=digest(sorted(training_units)) or
        len(library['candidates'])!=expected_candidates or set(library['candidates'])!=set(audit['cohorts']) or
        set(library['candidates'])!=set(library['shared_groups']) or set(library['candidates'])!=set(library['prior'])):
        raise ValueError('library fitting identity or candidate coverage mismatch')
    distribution(library['prior'])
    names=sorted({fit['maker_training_cohort'] for fit in audit['cohorts'].values()})
    mapping={name:'maker'+str(i) for i,name in enumerate(names)}
    groups={key:mapping[fit['maker_training_cohort']] for key,fit in audit['cohorts'].items()}
    sizes=Counter(groups.values())
    expected_prior={key:1/(len(sizes)*sizes[groups[key]]) for key in groups}
    if library['shared_groups']!=groups or library['prior']!=expected_prior:
        raise ValueError('library hierarchy or prior differs from its declared training construction')
    for key,program in library['candidates'].items():
        validate_program(program);fit=audit['cohorts'][key]
        selected=[{k:r[k] for k in ('unit','evidence','target')} for r in records
                  if r['maker_group']==fit['maker_training_cohort'] and r['purpose_group']==fit['purpose_training_cohort']]
        if (fit['converged'] is not True or fit['program_sha256']!=digest(program) or
            fit['training_records_sha256']!=digest(selected) or len({r['unit'] for r in selected})<minimum_units):
            raise ValueError('library parameter or cohort fit receipt mismatch')
    return True


def validate_choice(parameters,audit,records,l2):
    if (audit['converged'] is not True or audit['parameters_sha256']!=digest(parameters) or
        audit['training_records_sha256']!=digest(records) or audit['l2']!=l2 or parameters['individual'] is not False):
        raise ValueError('choice parameter or fitting-input receipt mismatch')
    return True


def train(directory,*,role,band,per_domain=4):
    directory=inside(directory)
    if role not in ('pilot','training') or type(per_domain) is not int or per_domain<1:
        raise ValueError('explicit training or discarded-pilot allocation required')
    if role=='training' and per_domain<4:
        raise ValueError('scientific library requires eight independent units per joint cohort')
    sources=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
                     REPO/'runners/__init__.py',REPO/'runners/readout_repair.py'])
    identity={'operation':'artifact-model-training-v1','role':role,'band':band,'per_domain':per_domain,
        'cell_identity':os.environ.get('S9_CELL_IDENTITY'),
        'source':sources,'views':['artifact','process_record'],'regularizers':list(REGULARIZERS),
        'adaptation_strengths':list(ADAPTATION_STRENGTHS),'program_regularizer':.01,
        'selection':'none here; all declared candidates retained for separate development selection'}
    with writer(directory):
        freeze(directory/'IDENTITY.json',identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed model package changed')
            return done
        if (directory/'FAILED.json').exists():
            raise ValueError('failed training attempt requires an explicit new lineage')
        started,cpu=time.monotonic(),time.process_time()
        write(directory/'RUNNING.json',{'identity_sha256':digest(identity),'at':datetime.now(timezone.utc).isoformat(),
                                      'cost_owner':'invocation plus parent scientific queue attempt receipt'})
        try:
            prepared={}
            for view in identity['views']:
                path=directory/(view+'-PREPARED.json')
                if path.exists():
                    data=read(path)
                else:
                    data=prepare(band=band,per_domain=per_domain,view=view)
                    freeze(path,data)
                validate_prepared(data,band=band,per_domain=per_domain,view=view)
                prepared[view]=data
            if [u['source_sha256'] for u in prepared['artifact']['units']]!=[u['source_sha256'] for u in prepared['process_record']['units']]:
                raise ValueError('evidence-view fits do not share the actual source worlds')
            library_path=directory/'LIBRARY.json'
            if not library_path.exists():
                library,audit=fit_library(prepared['artifact']['records'],
                    {u['unit'] for u in prepared['artifact']['units']},minimum_units=2*per_domain,l2=.01)
                freeze(directory/'LIBRARY_FIT.json',audit)
                freeze(library_path,library)
            elif not (directory/'LIBRARY_FIT.json').exists():
                raise ValueError('library parameters lack their fitting receipt')
            validate_library(read(library_path),read(directory/'LIBRARY_FIT.json'),prepared['artifact']['records'],
                {u['unit'] for u in prepared['artifact']['units']},minimum_units=2*per_domain)
            models={}
            for view,data in prepared.items():
                records=[{k:r[k] for k in ('unit','evidence','target')} for r in data['records']]
                unit_sizes=Counter(r['unit'] for r in records)
                counts={t:1. for t in TYPES}
                for row in records:
                    kind=row['target'].split(':')[0]
                    if kind in counts:counts[kind]+=1/unit_sizes[row['unit']]
                total=sum(counts.values())
                type_prior={t:v/total for t,v in counts.items()}
                freeze(directory/(view+'-TYPE_PRIOR.json'),type_prior)
                for l2 in REGULARIZERS:
                    key=view+'-l2-'+str(l2)
                    path=directory/(key+'.json')
                    if not path.exists():
                        parameters,audit=fit_choice(records,l2=l2,max_iterations=500)
                        freeze(directory/(key+'-FIT.json'),audit)
                        freeze(path,parameters)
                    elif not (directory/(key+'-FIT.json')).exists():
                        raise ValueError('choice model parameters lack their fitting receipt')
                    validate_choice(read(path),read(directory/(key+'-FIT.json')),records,l2)
                    models[key]={'parameters':path.relative_to(REPO).as_posix(),
                        'fit':(directory/(key+'-FIT.json')).relative_to(REPO).as_posix(),
                        'view':view,'l2':l2,'individual':False,
                        'adaptation_strength_candidates':list(ADAPTATION_STRENGTHS)}
            verify_sources(sources)
            outputs=closure([p for p in directory.glob('*.json') if p.name not in ('RUNNING.json','COMPLETE.json','FAILED.json')])
            done={'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(identity),'source':sources,
                'cell_identity':identity['cell_identity'],
                'role':role,'accepted':True,'training_only':True,'models':models,'candidate_programs':48,
                'independent_training_worlds':len(prepared['artifact']['units']),
                'supervised_boundaries_per_view':len(prepared['artifact']['records']),
                'outputs':outputs,'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,
                'gpu_seconds':0,'cost_scope':'this invocation; interruption cost requires the parent queue receipts',
                'heldout_predictions_scored':False,'reader_admission':False,'launch_accepted':False}
            freeze(directory/'COMPLETE.json',done)
            return done
        except BaseException:
            write(directory/'FAILED.json',{'identity_sha256':digest(identity),'source':sources,
                'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,
                'gpu_seconds':0,'error':traceback.format_exc()})
            raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--role',required=True,choices=('pilot','training'))
    parser.add_argument('--band',required=True,type=int)
    parser.add_argument('--per-domain',type=int,default=4)
    args=parser.parse_args()
    train(Path(args.root),role=args.role,band=args.band,per_domain=args.per_domain)
    print('Numerical training candidates complete; development selection and reader admission remain separate.',flush=True)


if __name__=='__main__':main()
