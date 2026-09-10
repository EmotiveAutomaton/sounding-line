"""Actual-package finite precision calibration, including the long task support.

DESIGN CHECK: I03/X02/X06/X07/X12; LESSONS 3--5, CONTROLS 6.
NULL: invalid components, unequal identical continuations, changed source or
package, incomplete variants or excessive numerical movement refuse acceptance.
ALTERNATIVE: all options survive the real scorer, ties and permutations are exact,
and the declared FP16 route stays within the unchanged .01 total-variation bound
against FP32 CPU and FP16 batch one. The historical 1e-6 judgment is also retained.
This calibrates fixed discarded inputs, never their scientific answers. Historical
BF16 failures remain preserved; that unused precision is not a new candidate.
"""
import argparse
from pathlib import Path
import time
import urllib.error
import uuid
from runners.stage9.common import REPO,ROOT,Units,closure,digest,file_hash,freeze,read
from runners.stage9.artifact_comparisons import checkpoint_call,audit_execution
from runners.stage9.model_pilot import examples,maker_series_case
from runners.stage9.neural_operations import training_package
from runners.stage9.reader_packages import reference_package
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident,post
from runners.stage9.queue import inside,verify_sources,writer
from runners.stage9.training_jobs import cell_identity

VARIANTS=(('float16','cuda',4),('float16','cuda',1),('float32','cpu',4))
TRANSPORT_SECONDS={'fp16_cuda':600,'fp32_cpu':1800,'cpu_capsule':1860}


def check_transport(identity):
    version=identity.get('operation')
    if version=='actual-package-precision-v2':
        actual=identity.get('transport_seconds')
        if (actual!=TRANSPORT_SECONDS or any(type(value) is not int for value in actual.values())):
            raise ValueError('calibration transport envelope changed')
    elif version=='actual-package-precision-v1':
        if 'transport_seconds' in identity:raise ValueError('historical calibration cannot acquire a new transport envelope')
    else:raise ValueError('unknown calibrated transport version')


def call_task(package,evidence,version='actual-package-precision-v2'):
    task={'operation':'choice','identity':{**package,'information_sha256':digest(evidence)}}
    if version=='actual-package-precision-v2':
        if package['device']=='cpu':task['request_timeout_seconds']=1800
    elif version!='actual-package-precision-v1':raise ValueError('unknown calibrated transport version')
    return task


def compare(predictions,inputs):
    names=['-'.join(map(str,v)) for v in VARIANTS]
    if not inputs or set(predictions)!=set(names) or any(set(v)!=set(inputs) for v in predictions.values()):
        raise ValueError('full identical precision fixture grid required')
    distances={}
    from runners.stage9.common import distribution
    for name,rows in predictions.items():
        distances[name]={}
        for key,evidence in inputs.items():
            probabilities=rows[key]
            distribution(probabilities)
            if set(probabilities)!=set(evidence['options']):raise ValueError('calibration omitted an actual option')
            reference=predictions['float32-cpu-4'][key]
            distribution(reference)
            if set(reference)!=set(probabilities):raise ValueError('precision supports differ')
            distances[name][key]=sum(abs(probabilities[k]-reference[k]) for k in probabilities)/2
    batch={key:sum(abs(predictions['float16-cuda-4'][key][k]-predictions['float16-cuda-1'][key][k])
                   for k in inputs[key]['options'])/2 for key in inputs}
    maximum=max([*distances['float16-cuda-4'].values(),*batch.values()])
    return {'distances_from_fp32_cpu':distances,'fp16_batch_distances':batch,
        'maximum_required_distance':maximum,'old_1e_minus6_pass':maximum<=1e-6,
        'amended_0_01_pass':maximum<=.01,'instrument_accepted':maximum<=.01,
        'meaning':'finite discarded fixture envelope; CPU reference changes device and precision, batch comparison holds both fixed'}


def context(directory,family,kind,training,scope,*,cell,source=None,version='actual-package-precision-v2'):
    """Construct the original discarded inputs and identity without writer/model execution."""
    directory=inside(directory)
    prefix='package-calibration-pilots' if scope=='pilot' else 'scientific-package-calibration'
    if scope not in ('pilot','scientific') or not directory.is_relative_to(ROOT/'private'/prefix):raise ValueError('calibration scope differs')
    if kind=='fitted':
        if training is None:raise ValueError('fitted calibration requires actual training')
        adapter,adapter_sha,fit_sha=training_package(training,family,scope)
    else:
        if training is not None:raise ValueError('reference calibration cannot borrow a trained identity')
        adapter,adapter_sha,fit_sha=reference_package(family,kind)
    from transformers import AutoTokenizer
    from runners.stage9.train import BASES
    base=BASES[family];tok=AutoTokenizer.from_pretrained(base['model'],revision=base['revision'],local_files_only=True,trust_remote_code=False)
    corpus_path=ROOT/'private/pilot'/(family+'-corpus.json');inputs={c['name']:c['evidence'] for c in examples(read(corpus_path))}
    long,metadata=maker_series_case(tok);inputs['long-distinct-series']=long
    if source is None:
        source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
            REPO/'runners/__init__.py',REPO/'runners/readout_repair.py',REPO/'runners/s3_lib.py',REPO/'runners/s4_lib.py',REPO/'runners/s5_lib.py'])
    else:
        extras={'runners/__init__.py','runners/readout_repair.py','runners/s3_lib.py','runners/s4_lib.py','runners/s5_lib.py'}
        files={p:sha for p,sha in source['files'].items()
            if p.startswith(('runners/stage9/','runners/stage7/','runners/stage8/','soundingline/')) or p in extras}
        source={'files':files,'sha256':digest(files)}
    identity={'cell_identity':cell,'operation':version,'scope':scope,'family':family,
        'package_kind':kind,'adapter_sha256':adapter_sha,'fitting_or_reference_sha256':fit_sha,
        'sources':source,'fixture_corpus_sha256':file_hash(corpus_path),'inputs_sha256':digest(inputs),
        'variants':VARIANTS,'maximum_context':4096,'maximum_support':128,'old_tolerance':1e-6,'amended_tolerance':.01,
        'long_context':metadata,'data_role':'discarded instrument fixtures; no scientific target scored'}
    if version=='actual-package-precision-v2':identity['transport_seconds']=dict(TRANSPORT_SECONDS)
    check_transport(identity)
    return identity,adapter,inputs


def run(directory,family,kind,training,scope):
    start,cpu=time.monotonic(),time.process_time();cell=cell_identity();directory=inside(directory)
    identity,adapter,inputs=context(directory,family,kind,training,scope,cell=cell)
    adapter_sha=identity['adapter_sha256'];source=identity['sources']
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed package calibration changed')
            return done
        freeze(directory/'INPUTS.json',inputs);all_predictions={};packages={};invalidity=[]
        for precision,device,batch in VARIANTS:
            key=f'{precision}-{device}-{batch}'
            config={'family':family,'adapter':str(adapter) if adapter is not None else None,'adapter_sha256':adapter_sha,
                'precision':precision,'device':device,'batch_size':batch,'max_context':4096,'max_support':128,'max_new_tokens':32}
            with resident(directory/'services'/uuid.uuid4().hex[:12],config) as (ready,token):
                packages[key]=ready['identity'];rows={}
                for name,evidence in inputs.items():
                    task=call_task(ready['identity'],evidence)
                    result=checkpoint_call(directory/'calls'/key/(name+'.json'),{'evidence':evidence,'task':task},
                        lambda:execute(evidence,task,ready['endpoint'],token,root=directory/'capsules',timeout=1860 if device=='cpu' else 900))
                    audit_execution(result)
                    if not result['accepted']:raise ValueError('invalid real calibration component retained in its immutable call')
                    probabilities=result['prediction']['probs']
                    if name.startswith('identical-stop-'):
                        if len(result['prediction']['ties'])!=len(evidence['options']) or any(abs(p-1/len(probabilities))>1e-12 for p in probabilities.values()):
                            raise ValueError('actual identical continuation tie failed')
                    rows[name]=probabilities
                original=inputs['distinct-maximum-support'];permuted={'prefix':original['prefix'],'options':dict(reversed(list(original['options'].items())))}
                task=call_task(ready['identity'],permuted)
                result=checkpoint_call(directory/'calls'/key/'permutation.json',{'evidence':permuted,'task':task},
                    lambda:execute(permuted,task,ready['endpoint'],token,root=directory/'capsules',timeout=1860 if device=='cpu' else 900))
                if not result['accepted'] or result['prediction']['probs']!=rows['distinct-maximum-support']:
                    raise ValueError('actual option permutation changed the readout')
                if key=='float16-cuda-4':
                    for attack in ('support_overflow','empty_continuation','wrong_identity'):
                        evidence={'prefix':'Next action: ','options':{'a':'STOP'}}
                        identity0={**ready['identity'],'information_sha256':digest(evidence)}
                        if attack=='support_overflow':evidence['options']={str(i):'STOP' for i in range(129)}
                        elif attack=='empty_continuation':evidence['options']['a']=''
                        else:identity0['adapter_sha256']='0'*64
                        identity0['information_sha256']=digest(evidence)
                        try:post(ready['endpoint'],token,'/infer',{'operation':'score',**evidence,'identity':identity0})
                        except urllib.error.HTTPError as exc:
                            if exc.code!=422:raise
                            invalidity.append({'attack':attack,'rejected':True})
                        else:raise ValueError('invalid actual package request was accepted')
                all_predictions[key]=rows;units.put(key,{'package':ready['identity'],'probabilities':rows})
        result=compare(all_predictions,inputs)
        freeze(directory/'PACKAGES.json',packages);freeze(directory/'CALIBRATION.json',result);freeze(directory/'INVALIDITY.json',invalidity)
        verify_sources(source)
        done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'instrument_only':True,
            'instrument_accepted':result['instrument_accepted'],'old_1e_minus6_pass':result['old_1e_minus6_pass'],
            'family':family,'package_kind':kind,'adapter_sha256':adapter_sha,'data_role':'pilot',
            'wall_seconds':time.monotonic()-start,'parent_cpu_seconds':time.process_time()-cpu,
            'outputs':closure([directory/p for p in ('IDENTITY.json','INPUTS.json','PACKAGES.json','CALIBRATION.json','INVALIDITY.json','units','calls','capsules','services')]),
            'scientific_admission':False,'scope':'actual package, original and long discarded supports; no scientific competence claim'}
        freeze(directory/'COMPLETE.json',done);return done


def score_package(package):
    """Generation sampling and its output cap do not enter the score operation.

    Every other field is retained, including the actual base/tokenizer bytes,
    adapter, installed libraries, attention, precision, device, batching and bounds.
    This projection licenses no generation-precision or competence transfer.
    """
    required={'model','revision','adapter_sha256','base_files','base_files_sha256',
        'scorer_sha256','scorer_sources','precision','device','batch_size','max_context',
        'max_support','renderer','attention_implementation','long_context_batch_rule',
        'torch','transformers','peft','generation','max_new_tokens'}
    if not required <= set(package):raise ValueError('incomplete actual score package')
    if digest(package['base_files'])!=package['base_files_sha256']:
        raise ValueError('base/tokenizer file identity changed')
    if package['scorer_sources']['sha256']!=package['scorer_sha256']:
        raise ValueError('scorer closure identity changed')
    return {k:v for k,v in package.items() if k not in ('generation','max_new_tokens')}


def compatible(calibrated,target):
    if score_package(calibrated)!=score_package(target):
        raise ValueError('calibration cannot transfer to a different actual score package')


def checked_calibration(directory,target):
    """Read the live decision and reconstruct all fixed calls before consuming it."""
    directory=inside(directory);identity=read(directory/'IDENTITY.json');done=read(directory/'COMPLETE.json')
    check_transport(identity)
    if (identity.get('operation') not in ('actual-package-precision-v1','actual-package-precision-v2') or done.get('execution_complete') is not True
        or done['identity_sha256']!=digest(identity) or done['cell_identity']!=identity['cell_identity']
        or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']):
        raise ValueError('calibration completion, identity or output closure changed')
    inputs=read(directory/'INPUTS.json');packages=read(directory/'PACKAGES.json')
    expected=['-'.join(map(str,v)) for v in VARIANTS]
    if (digest(inputs)!=identity['inputs_sha256'] or set(packages)!=set(expected)
        or identity['old_tolerance']!=1e-6 or identity['amended_tolerance']!=.01
        or identity['maximum_context']!=4096 or identity['maximum_support']!=128):
        raise ValueError('calibration grid or fixed envelope changed')
    compatible(packages['float16-cuda-4'],target)
    predictions={};common=None
    for precision,device,batch in VARIANTS:
        key=f'{precision}-{device}-{batch}';package=packages[key];scoped=score_package(package)
        if (package['precision'],package['device'],package['batch_size'])!=(precision,device,batch):
            raise ValueError('actual precision variant differs')
        base={k:v for k,v in scoped.items() if k not in ('precision','device','batch_size')}
        if common is not None and common!=base:raise ValueError('calibration variants changed more than precision/device/batching')
        common=base;rows={}
        for name,evidence in inputs.items():
            task=call_task(package,evidence,identity['operation'])
            result=checkpoint_call(directory/'calls'/key/(name+'.json'),{'evidence':evidence,'task':task},None,resume_only=True)
            audit_execution(result)
            if result['accepted'] is not True:raise ValueError('calibration contains an invalid component')
            probabilities=result['prediction']['probs']
            if name.startswith('identical-stop-') and (len(result['prediction']['ties'])!=len(evidence['options'])
                or any(abs(p-1/len(probabilities))>1e-12 for p in probabilities.values())):
                raise ValueError('saved identical continuation tie failed')
            rows[name]=probabilities
        original=inputs['distinct-maximum-support']
        evidence={'prefix':original['prefix'],'options':dict(reversed(list(original['options'].items())))}
        task=call_task(package,evidence,identity['operation'])
        result=checkpoint_call(directory/'calls'/key/'permutation.json',{'evidence':evidence,'task':task},None,resume_only=True)
        audit_execution(result)
        if result['accepted'] is not True or result['prediction']['probs']!=rows['distinct-maximum-support']:
            raise ValueError('saved option permutation differs')
        unit=read(directory/'units'/(digest(key)+'.json'))
        if (unit.get('complete') is not True or unit!={'identity':digest(identity),'key':key,'complete':True,
                'row':{'package':package,'probabilities':rows}}):
            raise ValueError('calibration variant unit differs from actual calls')
        predictions[key]=rows
    invalidity=[{'attack':name,'rejected':True} for name in ('support_overflow','empty_continuation','wrong_identity')]
    if read(directory/'INVALIDITY.json')!=invalidity:raise ValueError('actual invalidity checks incomplete')
    result=compare(predictions,inputs)
    if (result!=read(directory/'CALIBRATION.json') or result['instrument_accepted']!=done['instrument_accepted']
        or result['old_1e_minus6_pass']!=done['old_1e_minus6_pass']):
        raise ValueError('live calibration decision does not reproduce')
    return {'calibration_complete_sha256':file_hash(directory/'COMPLETE.json'),
        'score_package_sha256':digest(score_package(target)),**result,
        'scientific_admission':False,'generation_precision_calibrated':False}


def argument_parser():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--family',choices=('qwen','smollm'),required=True);p.add_argument('--package-kind',choices=('fitted','base','archive'),required=True)
    p.add_argument('--training',type=Path);p.add_argument('--scope',choices=('pilot','scientific'),required=True)
    return p


if __name__=='__main__':
    a=argument_parser().parse_args();run(a.output,a.family,a.package_kind,a.training,a.scope)
