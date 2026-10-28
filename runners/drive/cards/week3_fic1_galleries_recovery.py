"""First FIC1 gallery loader repair: compare profile identities, not list order.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-27.
NULL and ALTERNATIVE both require identical complete keyed predecessor records.
Top-level order is immaterial; duplicate keys, changed fields or missing records
must fail. Profile session chronology, source seals, covariates and every
numerical operation stay unchanged. No human identification score is computed.
"""
from pathlib import Path
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,freeze
from . import week3_fic1_galleries as base
from .timing_p6 import gzread
from .timing_pmap_source import completed

CONFIG=base.CONFIG
CONSTRUCTED=base.CONSTRUCTED


def keyed_profiles(rows):
    out={}
    for row in rows:
        key=(row['writer'],row['genre'],row['half'])
        if key in out:raise ValueError('duplicate predecessor profile')
        out[key]=row
    if not out:raise ValueError('empty predecessor profiles')
    return out


def load(inputs,config):
    if config==CONSTRUCTED:return base.load(inputs,config)
    if config!=CONFIG or set(inputs)!={'prefix_completion','feature_completion'}:raise ValueError('fixed completed predecessors required')
    bindings={}
    def artifact(which,rel):
        terminal=Path(inputs[which]).resolve();path=terminal.parent/rel
        completed(terminal,path);bindings[str(terminal)]=filehash(terminal);bindings[str(path)]=filehash(path)
        return gzread(path) if path.suffix=='.gz' else read(path)
    pp=artifact('prefix_completion','PLAN.json');fp=artifact('feature_completion','PLAN.json')
    if pp['module']!='runners.drive.cards.week3_fic1_prefixes' or pp['config']!=base.prefixes_source.CONFIG or fp['module']!='runners.drive.cards.week3_fic1_features' or fp['config']!=base.features.CONFIG:
        raise ValueError('unexpected gallery predecessor')
    if Path(pp['inputs']['feature_completion']).resolve()!=Path(inputs['feature_completion']).resolve():raise ValueError('prefix/feature lineage differs')
    summary=artifact('prefix_completion','output/SUMMARY.json')
    if not summary['exact_occurrence_replay'] or summary['identification_computed']:raise ValueError('unexpected prefix scope')
    index=artifact('feature_completion','output/SESSION_INDEX.json');rows=[]
    for item in index:
        r=artifact('feature_completion','output/'+item['file'])
        if r['session']!=item['session'] or filehash(Path(inputs['feature_completion']).parent/'output'/item['file'])!=item['sha256']:raise ValueError('feature session binding differs')
        rows.append(r)
    groups=artifact('prefix_completion','output/PROFILES.json')
    if keyed_profiles(groups)!=keyed_profiles(artifact('feature_completion','output/PROFILES.json')):raise ValueError('predecessor memberships differ')
    dictionary=artifact('prefix_completion','output/DICTIONARY.json')
    if dictionary!=artifact('feature_completion','output/DICTIONARY.json'):raise ValueError('predecessor dictionaries differ')
    return dict(rows=rows,profiles=groups,prefixes=artifact('prefix_completion','output/PREFIX_FEATURES.json'),dictionary=dictionary),bindings


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=1):
        data,bindings=load(inputs,config);result=base.prepare(data,config)
    summary=dict(card=CONFIG['card'],constructed=config['mode']=='constructed',sessions=len(data['rows']),
        profiles=len(data['profiles']),writers=config['writers'],all_profiles_retained=True,
        support={k:dict(supported_writers=v['supported_writers'],unsupported_writers=len(v['unsupported'])) for k,v in result['support'].items()},
        length_curve_common_writers={k:len(v) for k,v in result['length_curve_common_writers'].items()},
        length_covariate_fitted=True,identification_computed=False,controls_computed=False,
        full_calibration_complete=False,scientific_admission=False,auth_requests_prepared=False)
    for name,value in [('GALLERIES.json',result),('SUMMARY.json',summary),('BINDING.json',dict(config=config,inputs=bindings))]:
        path=output/name
        if verification:
            if read(path)!=value:raise ValueError('full gallery replay differs: '+name)
        else:freeze(path,value)
    if verification:return dict(verified=True,complete_input_replay=True,all_galleries_recomputed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
