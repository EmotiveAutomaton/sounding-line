"""Identified, resumable operation-specific neural reader execution.

DESIGN CHECK: C01/C02/C06/C08/X01/X02/X08/X11/X12; LESSONS 3--5.
NULL: changed source/case/package, reused pilot weights, missing calls or partial
units cannot close; invalid model actions remain behavior failures on their assigned
units. ALTERNATIVE: the same actual operation traverses a discarded real-model
rehearsal and scientific execution with complete saved inputs and inference receipts.
Bands: completed predictions with separate execution validity, or implementation
refusal. No per-artifact score, local capability or broad admission is computed here.
"""
import argparse
from functools import partial
from pathlib import Path
import time
import uuid

from runners.stage9.artifact_comparisons import audit_execution,checkpoint_call,validate_cases
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.construction import Replay
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.recipes import POP
from runners.stage9.rollout_operations import (matched_altered_prefix,public_input,rollout,state_identity)
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident
from runners.stage9.train import BASES
from runners.stage9.training_jobs import cell_identity,FITS,training_root

OPERATIONS={
    'offered':{'mode':'offered','horizon':16,'reset_every':0,'view':'process_record'},
    'environment_outcome':{'mode':'environment_outcome','horizon':16,'reset_every':0,'view':'process_record'},
    'self_outcome':{'mode':'self_outcome','horizon':16,'reset_every':0,'view':'process_record'},
    'reset_environment':{'mode':'environment_outcome','horizon':16,'reset_every':4,'view':'process_record'},
    'artifact_environment':{'mode':'environment_outcome','horizon':16,'reset_every':0,'view':'artifact'},
    'prefix_match':None,
    'finite_queries':None,
    'broad_original':None,
    'broad_expanded':None,
    'broad_historical':None,
    'historical_prediction':None,
    'local_repair_artifact':None,
    'local_repair_process':None,
    'genuine_choice':None,
    'process_choice':None,
    'artifact_choice':None,
    'supplied_kernel':None,
    'ambiguity':None,
}
BROAD={'broad_original':'original','broad_expanded':'expanded','broad_historical':'historical_replay'}


def generation_settings(operation):
    from runners.stage9.generation_policy import LEGACY,GREEDY
    return (336,LEGACY) if operation in BROAD else (32,GREEDY)


def training_package(directory,family,scope):
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=read(directory/'COMPLETE.json')
    if (identity.get('family')!=family or identity.get('base')!=BASES[family]
        or done.get('identity_sha256')!=digest(identity)):
        raise ValueError('operation training identity differs from pinned family')
    if scope=='scientific':
        source=read(directory/'SCIENTIFIC_INPUT.json')
        if (identity.get('split')!='training' or (family,source['recipe'],identity['seed']) not in FITS
            or source['seed']!=identity['seed'] or source['family']!=family
            or source['corpus_sha256']!=identity['corpus_sha256']
            or identity.get('epochs')!=3 or len(done['curve'])!=3
            or done['curve'][-1]['updates']!=600 or any(row['n']!=96 for row in done['curve'])):
            raise ValueError('scientific operation requires the complete declared factorial fit')
        if (directory!=training_root(family,source['recipe'],identity['seed'])
            or file_hash(ROOT/'private/scientific-recipes'/family/(source['recipe']+'.json'))!=source['corpus_sha256']):
            raise ValueError('scientific fitting namespace or source corpus changed')
    elif scope=='pilot':
        # Both entries are already completed discarded fits. No new training or
        # scientific checkpoint is selected by choosing a rehearsal input.
        full_name={'qwen':'qwen-run2','smollm':'smollm-run1'}[family]
        catalog={
            ROOT/'private/training-handler-pilots/v2'/family/'fit':
                (997901,1,[8],64,ROOT/'private/pilot-dose-v3'/family/'mixed.json'),
            ROOT/'pilot'/full_name:
                (99001,3,[200,400,600],1600,ROOT/'private/pilot'/(family+'-corpus.json')),
        }
        if directory not in catalog:
            raise ValueError('operation rehearsal requires an explicitly registered discarded fit')
        seed,epochs,updates,examples,corpus=catalog[directory]
        if (identity.get('split')!='pilot' or identity.get('seed')!=seed or identity.get('epochs')!=epochs
            or [r['updates'] for r in done['curve']]!=updates or any(r['n']!=80 for r in done['curve'])):
            raise ValueError('discarded operation fitting profile differs from its actual completed recipe')
        prepared=read(corpus)
        if (identity.get('corpus_sha256')!=file_hash(corpus) or len(prepared['examples'])!=examples
            or prepared['split']!='pilot' or len(prepared['validation_choices'])!=80):
            raise ValueError('discarded operation fitting corpus or exposure changed')
    else:
        raise ValueError('undeclared operation scope')
    adapter=inside(directory/done['selected_checkpoint'],directory)
    if closure([adapter])['sha256']!=done['selected_checkpoint_sha256']:
        raise ValueError('operation checkpoint differs from fitted selection')
    return adapter,done['selected_checkpoint_sha256'],file_hash(directory/'COMPLETE.json')


def case_inputs(directory,scope,limit):
    directory=inside(directory);complete=read(directory/'COMPLETE.json')
    if complete.get('accepted') is not True or complete.get('construction_only') is not True:
        raise ValueError('operation cases lack valid complete construction')
    if closure([REPO/p for p in complete['outputs']['files']])!=complete['outputs']:
        raise ValueError('operation construction outputs changed')
    role=complete['role']
    if (scope=='pilot' and (role!='pilot' or limit!=2)
        or scope=='scientific' and (role not in ('development','discovery') or limit!=0)):
        raise ValueError('scientific operation cannot subset or borrow discarded cases')
    cases=read(directory/'CASES.json');validate_cases(cases,role)
    if len(cases)!=complete['selected_series']:raise ValueError('operation construction count differs')
    if scope=='pilot':
        # Explicit balanced rehearsal: one assigned series per actual domain.
        cases=[next(c for c in cases if c['source_worlds'][0]['domain']==domain) for domain in POP.DOMAINS]
    return cases,role,file_hash(directory/'COMPLETE.json')


def prefix_unit(world,call):
    boundary=3;pair=matched_altered_prefix(world,boundary)
    if not pair['realized']:
        return {'realized':False,'reason':pair['reason'],'matched_generated_state':False,'calls':[]}
    predictions={};calls=[]
    for label in ('genuine','altered'):
        evidence=public_input(world,pair[label],offered=True)
        result=call(evidence,{'operation':'choice'},label)
        predictions[label]=result;calls.append(result)
    generated=rollout(world,lambda evidence,args,i:call(evidence,args,'generated-'+str(i)),
                      mode='environment_outcome',horizon=boundary)
    # Only the first three actual interactions can realize the declared matched
    # state; a failed or early-stopped generation never receives a replacement.
    prefix=[r['actual_event'] for r in generated['attempts'][:boundary] if r['actual_event'] is not None]
    matched=(len(prefix)==boundary and state_identity(Replay(world,prefix,extend_visible=True))==pair['state_sha256'])
    if matched:
        evidence=public_input(world,prefix,offered=True)
        result=call(evidence,{'operation':'choice'},'generated-choice')
        predictions['generated']=result;calls.append(result)
    return {'realized':True,'boundary':boundary,'pair':pair,'predictions':predictions,
        'generated':generated,'matched_generated_state':matched,
        'generated_condition_reason':None if matched else 'generated prefix does not reach the same operative state',
        'calls':calls,'scope':'generated-history contrast only where the exact state match realizes; all assignments retained'}


def unit_result(case,operation,call):
    world=case['source_worlds'][0]
    if operation=='historical_prediction':
        from runners.stage9.historical_prediction import evaluate_unit
        result=evaluate_unit(case,call)
    elif operation=='supplied_kernel':
        from runners.stage9.supplied_operations import evaluate_unit
        result=evaluate_unit(case,call)
    elif operation=='ambiguity':
        from runners.stage9.ambiguity_operations import evaluate_unit
        result=evaluate_unit(case,call)
    elif operation in ('genuine_choice','process_choice','artifact_choice'):
        from runners.stage9.prospective_choice import evaluate_unit
        result=evaluate_unit(case,operation,call)
    elif operation in ('local_repair_artifact','local_repair_process'):
        from runners.stage9.local_repair import evaluate_unit
        result=evaluate_unit(case,'artifact' if operation=='local_repair_artifact' else 'process_record',call)
    elif operation in BROAD:
        evidence=public_input(world,[],view='process_record')
        seed=int(digest({'s9_full_log_sampling':case['unit']})[:8],16)
        result={'call':call(evidence,{'operation':'generate','max_new_tokens':336,'seed':seed},'full-log'),
            'population':BROAD[operation],'max_lines':28,'input_sha256':digest(evidence),'sampling_seed':seed,
            'scope':'uninterrupted sampled full log; no environment outcomes, action offers, masks or state resets'}
    elif operation=='finite_queries':
        from runners.stage9.finite_queries import evaluate_unit
        result=evaluate_unit(world,call)
    else:
        result=prefix_unit(world,call) if operation=='prefix_match' else rollout(world,call,**OPERATIONS[operation])
    return {'unit':case['unit'],'domain':world['domain'],'case_sha256':digest(case),'operation':operation,
        'law':world['state']['names']['law'],'role':case['role'],'result':result}


def validate_complete(directory,identity):
    complete=read(directory/'COMPLETE.json')
    if (complete['identity_sha256']!=digest(identity) or complete['cell_identity']!=identity['cell_identity']
        or closure([REPO/p for p in complete['outputs']['files']])!=complete['outputs']):
        raise ValueError('completed neural operation identity or outputs changed')
    return complete


def request_task(evidence,arguments,package):
    if arguments.get('operation')=='execute_program_mixture':
        return {**arguments,'information_sha256':digest(evidence)}
    return {**arguments,'identity':{**package,'information_sha256':digest(evidence)}}


def context(directory,*,cell,operation,family,training,cases,scope,limit=0,package_kind='fitted',
            recipe_selection=None,selection_manifest=None,selection_queue=None,selection_seed=None,
            source=None):
    """Read the exact execution inputs without writing or starting a reader.

    Final inspection supplies the original committed source closure; execution
    obtains the current closure. Neither path changes the original case rules.
    """
    directory=inside(directory)
    if operation not in OPERATIONS:raise ValueError('undeclared neural operation')
    if scope=='pilot' and not directory.is_relative_to(ROOT/'private/neural-operation-pilots'):
        raise ValueError('discarded operation output must remain in its rehearsal namespace')
    if scope=='scientific' and not directory.is_relative_to(ROOT/'private/scientific-neural-operations'):
        raise ValueError('scientific operation output must remain in its scientific namespace')
    from runners.stage9.selected_recipe import execution_selection
    training,selection_provenance=execution_selection(recipe_selection,selection_manifest,selection_queue,selection_seed,
        training=training,package_kind=package_kind,family=family,scope=scope)
    if package_kind=='fitted':
        if training is None:raise ValueError('fitted reader requires its actual training directory')
        adapter,adapter_sha,fit_sha=training_package(training,family,scope)
    else:
        from runners.stage9.reader_packages import reference_package
        if training is not None:raise ValueError('reference reader cannot also name a training directory')
        adapter,adapter_sha,fit_sha=reference_package(family,package_kind)
    world_plan=None
    if operation=='historical_prediction':
        from runners.stage9.historical_prediction import checked_inputs
        if limit!=(4 if scope=='pilot' else 0):raise ValueError('historical prediction cannot alter its complete cohort')
        selected,role,cases_sha=checked_inputs(cases,scope)
    elif operation in BROAD:
        if operation=='broad_historical':
            from runners.stage9.historical_generation import checked_inputs
        else:
            from runners.stage9.generation_cases import checked_inputs
        if limit!=(2 if scope=='pilot' else 0):raise ValueError('broad generation cannot alter its complete cohort')
        selected,role,cases_sha,world_plan=checked_inputs(cases,scope,BROAD[operation])
    else:
        selected,role,cases_sha=case_inputs(cases,scope,limit)
    source_units=[case['unit'] for case in selected];projection_groups=None
    if operation=='finite_queries':
        from runners.stage9.finite_queries import group_cases
        selected,projection_groups=group_cases(selected)
    if source is None:
        source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
            REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    else:
        # The queue may also archive external parser helpers. Preserve the exact
        # operation source scope rather than widening historical identities.
        extras={'runners/__init__.py','runners/readout_repair.py','runners/s3_lib.py',
                'runners/s4_lib.py','runners/s5_lib.py'}
        files={p:sha for p,sha in source['files'].items()
               if p.startswith(('runners/stage9/','runners/stage7/','runners/stage8/','soundingline/')) or p in extras}
        source={'files':files,'sha256':digest(files)}
    maximum,generation=generation_settings(operation)
    identity={'cell_identity':cell,'operation':operation,'settings':OPERATIONS[operation],'scope':scope,'family':family,
        'package_kind':package_kind,'training_complete_sha256':fit_sha,'adapter_sha256':adapter_sha,'cases_complete_sha256':cases_sha,
        'units':[c['unit'] for c in selected],'original_source_units':source_units,
        'projection_groups':projection_groups,'role':role,'sources':source,'precision':'float16',
        'max_context':4096,'max_support':128,'generation':generation,'max_new_tokens':maximum}
    if selection_provenance is not None:identity['recipe_selection']=selection_provenance
    return identity,adapter,selected,world_plan


def run(directory,*,operation,family,training,cases,scope,limit=0,package_kind='fitted',
        recipe_selection=None,selection_manifest=None,selection_queue=None,selection_seed=None):
    started,cpu=time.monotonic(),time.process_time();directory=inside(directory)
    identity,adapter,selected,world_plan=context(directory,cell=cell_identity(),operation=operation,
        family=family,training=training,cases=cases,scope=scope,limit=limit,package_kind=package_kind,
        recipe_selection=recipe_selection,selection_manifest=selection_manifest,
        selection_queue=selection_queue,selection_seed=selection_seed)
    cell=identity['cell_identity'];sources=identity['sources'];adapter_sha=identity['adapter_sha256']
    maximum=identity['max_new_tokens'];generation=identity['generation']
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():return validate_complete(directory,identity)
        for name in ('calls','capsules','units'):(directory/name).mkdir(exist_ok=True)
        config={'family':family,'adapter':str(adapter) if adapter is not None else None,'adapter_sha256':adapter_sha,'precision':'float16',
                'device':'cuda','batch_size':4,'max_context':4096,'max_support':128,'max_new_tokens':maximum,
                'generation':generation}
        with resident(directory/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
            freeze(directory/'PACKAGE.json',ready['identity'])
            def call(case,evidence,arguments,index,*,resume_only=False):
                task=request_task(evidence,arguments,ready['identity'])
                path=directory/'calls'/case['unit'][:16]/('call-'+digest(index)[:16]+'.json')
                def invoke():
                    if arguments.get('operation')=='execute_program_mixture':
                        from runners.stage9.kernel_runtime import execute as execute_kernel
                        return execute_kernel(evidence,task,root=directory/'capsules')
                    return execute(evidence,task,ready['endpoint'],token,root=directory/'capsules')
                return checkpoint_call(path,{'evidence':evidence,'task':task},
                    invoke,resume_only=resume_only)
            for case in selected:
                old=units.get(case['unit'])
                rebuilt=unit_result(case,operation,partial(call,case,resume_only=old is not None))
                if old is not None and digest(rebuilt)!=digest(old):raise ValueError('resumed operation unit differs')
                units.put(case['unit'],rebuilt)
        # Verify whole units again through the saved-input path, with no inference.
        for case in selected:
            expected=unit_result(case,operation,partial(call,case,resume_only=True))
            if digest(expected)!=digest(units.get(case['unit'])):raise ValueError('fresh operation reconstruction differs')
        calls=[read(p)['result'] for p in sorted((directory/'calls').rglob('*.json'))]
        for result in calls:
            audit_execution(result)
            if read(Path(result['capsule'])/'out/access.json')!=result['access']:
                raise ValueError('operation capsule access receipt differs')
        output_names=['IDENTITY.json','PACKAGE.json','units','calls','capsules','services']
        if operation=='historical_prediction':
            from runners.stage9.historical_prediction import summarize
            from runners.stage9.scoring import score_json
            analysis=summarize(selected,[units.get(case['unit'])['result'] for case in selected],scope)
            freeze(directory/'HISTORICAL_PREDICTION.json',score_json(analysis))
            output_names.append('HISTORICAL_PREDICTION.json')
        if operation in ('artifact_choice','process_choice'):
            from runners.stage9.confirmation_neural import discovery_forecasts
            forecasts=discovery_forecasts(selected,[units.get(case['unit']) for case in selected],operation)
            freeze(directory/'FORECASTS.json',forecasts)
            output_names.append('FORECASTS.json')
        if operation in BROAD:
            from runners.stage9.generation_analysis import summarize
            predictions=[units.get(case['unit'])['result']['call'] for case in selected]
            analysis=summarize([c['source_worlds'][0] for c in selected],predictions,
                world_plan['reference_scores'],population=BROAD[operation],scope=scope)
            freeze(directory/'GENERATION.json',analysis)
            output_names.append('GENERATION.json')
        verify_sources(sources)
        receipt={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,
            'all_reader_calls_valid':all(r['accepted'] for r in calls),'expected_units':len(selected),
            'completed_units':len(units.all()),'reader_calls':len(calls),'operation':operation,'scope':scope,
            'wall_seconds':time.monotonic()-started,'parent_cpu_seconds':time.process_time()-cpu,
            'cpu_scope':'parent process only; child/model execution not attributed to this CPU total',
            'outputs':closure([directory/p for p in output_names]),
            'capability':'not evaluated','scientific_admission':False,'disposition':'DESCRIPTIVE'}
        if receipt['completed_units']!=len(selected):raise ValueError('operation has extra or missing units')
        freeze(directory/'COMPLETE.json',receipt)
        return receipt


def argument_parser():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True);p.add_argument('--operation',choices=OPERATIONS,required=True)
    p.add_argument('--family',choices=BASES,required=True);p.add_argument('--training',type=Path)
    p.add_argument('--package-kind',choices=('fitted','base','archive'),default='fitted')
    p.add_argument('--cases',type=Path,required=True);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    p.add_argument('--limit',type=int,default=0)
    for name in ('recipe-selection','selection-manifest','selection-queue'):p.add_argument('--'+name,type=Path)
    p.add_argument('--selection-seed',type=int)
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,operation=a.operation,family=a.family,training=a.training,cases=a.cases,scope=a.scope,
        limit=a.limit,package_kind=a.package_kind,recipe_selection=a.recipe_selection,selection_manifest=a.selection_manifest,
        selection_queue=a.selection_queue,selection_seed=a.selection_seed)
