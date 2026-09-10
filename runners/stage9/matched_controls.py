"""Construct wrong-maker prior works at exactly matched public conditions.

DESIGN CHECK: M01/M04/X01/X03/X04/X08; LESSONS 3--5, CONTROLS 2/6.
NULL: relabeling a maker cannot manufacture changed behavior; altered future query
truth cannot change a control built only from earlier works. ALTERNATIVE: an actual
different persistent maker is executed under the same topics, tools, audience,
deadline, document structure and per-work purpose. Exact context or split mismatch
invalidates the control; naturally identical observed behavior is retained.

The existing constructor supplies the counterfactual. Candidate maker factors are
chosen before its trajectories, using only earlier conditions and split membership.
Beliefs may differ as part of the alternative maker. Length and realized behavior
are outcomes and are recorded, not searched to force a reader effect. This is an
exact public-condition construction control, not a token-length-matched control or
a claim about a naturally sampled other person. No target work is an input here.
"""
import argparse
from datetime import datetime,timezone
import itertools
import os
from pathlib import Path
import time

from .artifact_preparation import work
from .artifact_training import LAWS,RESIDUES
from .common import REPO,Units,closure,digest,file_hash,freeze,read,write
from .construction import W,register
from .queue import inside,verify_sources,writer
from .recipes import make_world_ext,parameter_partition
from .series_cases import TERMINAL,content_identity

FACTORS=('law','residue','tendency')


def parameter_stub(original,candidate,belief):
    return {'shape':original['shape'],'goal_name':original['goal_name'],
            'state':{'names':dict(zip(FACTORS,candidate),belief=belief)}}


def choose(earlier,role,key):
    if role not in ('pilot','training','development','discovery') or not key or not earlier:
        raise ValueError('nonreserve role, independent namespace and earlier works required')
    expected='training' if role=='pilot' else role
    original=tuple(earlier[0]['state']['names'][k] for k in FACTORS)
    if any(tuple(w['state']['names'][k] for k in FACTORS)!=original or parameter_partition(w)!=expected for w in earlier):
        raise ValueError('original maker or source partition differs across earlier works')
    # The original/secondary law pair shares a partition role, so at least one
    # distinct candidate has the original belief's admissible split in every work.
    candidates=sorted((c for c in itertools.product(LAWS,RESIDUES,W.TENDENCIES) if c!=original),
                      key=lambda c:digest({'key':key,'maker':c}))
    for candidate in candidates:
        beliefs=[]
        for old in earlier:
            allowed=[b for b in W.BELIEFS if parameter_partition(parameter_stub(old,candidate,b))==expected]
            if not allowed:break
            beliefs.append(min(allowed,key=lambda b:digest({'key':key,'earlier_lid':old['lid'],'belief':b})))
        else:return {'original':dict(zip(FACTORS,original)),'alternative':dict(zip(FACTORS,candidate)),
                     'beliefs':beliefs,'role':role,'key':key,'selection_reads':'earlier initial conditions and partition only'}
    raise ValueError('no different maker fits every declared earlier-work partition')


def construct(earlier,role,key):
    register();plan=choose(earlier,role,key);worlds=[]
    for i,old in enumerate(earlier):
        alt=plan['alternative']
        new=make_world_ext(old['lid'],old['domain'],old['shape'],goal=old['goal_name'],
            law_name=alt['law'],residue=alt['residue'],tendency=alt['tendency'],belief=plan['beliefs'][i],
            forced_cext=old['state']['external_context'],owner_all=old['goal_name'],finish=False,
            salt='stage9-other-maker:'+key,no_change=old.get('no_change',False))
        new['goal_name']=old['goal_name'];worlds.append(new)
    views={v:[work(w,w['trajectory']['steps'],v,w['trajectory']['stop_kind'] in TERMINAL) for w in worlds]
           for v in ('artifact','process_record')}
    result={'plan':plan,'worlds':worlds,'sources':[content_identity(w) for w in worlds],'views':views}
    validate(earlier,result,role,key,rebuild=False)
    return result


def validate(earlier,result,role,key,*,rebuild=True):
    register();expected='training' if role=='pilot' else role
    if result['plan']!=choose(earlier,role,key) or len(result['worlds'])!=len(earlier):
        raise ValueError('matched-maker plan or source count differs')
    source_hashes=[content_identity(w) for w in result['worlds']]
    if source_hashes!=result['sources'] or len(set(source_hashes))!=len(source_hashes):
        raise ValueError('duplicate or changed wrong-maker source content')
    for i,(old,new) in enumerate(zip(earlier,result['worlds'])):
        if (parameter_partition(new)!=expected or new['domain']!=old['domain'] or new['shape']!=old['shape'] or
            new['goal_name']!=old['goal_name'] or new['doc']!=old['doc'] or new['inventory']!=old['inventory'] or
            new['state']['external_context']!=old['state']['external_context'] or
            {k:new['state']['names'][k] for k in FACTORS}!=result['plan']['alternative']):
            raise ValueError('control changes matched conditions or declared maker/split')
        for view in ('artifact','process_record'):
            actual=work(new,new['trajectory']['steps'],view,new['trajectory']['stop_kind'] in TERMINAL)
            if actual!=result['views'][view][i] or actual['context']!=work(old,[],view)['context']:
                raise ValueError('wrong-maker evidence is not the exact public projection')
    # Compare the actual durable format. Constructor tuples and JSON arrays
    # represent the same scheduled change; changed values must still refuse.
    if rebuild and digest(construct(earlier,role,key))!=digest(result):
        raise ValueError('saved wrong-maker worlds do not reproduce from their initial conditions')
    return True


def run(directory,cases_path,*,role,key):
    started,cpu=time.monotonic(),time.process_time()
    cell=os.environ.get('S9_CELL_IDENTITY')
    if role!='pilot' and (not cell or len(cell)!=64):raise ValueError('scientific control preparation requires identified queue')
    directory,cases_path=inside(directory),inside(cases_path)
    parent=read(cases_path.parent/'COMPLETE.json')
    if parent.get('accepted') is not True or parent['role']!=role or closure([REPO/p for p in parent['outputs']['files']])!=parent['outputs']:
        raise ValueError('case preparation incomplete, changed or wrong split')
    from .artifact_comparisons import validate_cases
    cases=read(cases_path);original_sources=validate_cases(cases,role)
    source=closure([REPO/'runners/stage9',REPO/'runners/stage7',REPO/'runners/stage8',REPO/'soundingline',
                    REPO/'runners/__init__.py',REPO/'runners/readout_repair.py'])
    identity={'operation':'public-condition-matched-other-maker-v1','role':role,'key':key,'cell_identity':cell,
              'source':source,'case_completion_sha256':file_hash(cases_path.parent/'COMPLETE.json'),
              'case_sha256':file_hash(cases_path),'units':[c['unit'] for c in cases]}
    with writer(directory):
        units=Units(directory,identity)
        if (directory/'COMPLETE.json').exists():
            done=read(directory/'COMPLETE.json')
            if done['identity_sha256']!=digest(identity) or closure([REPO/p for p in done['outputs']['files']])!=done['outputs']:
                raise ValueError('completed matched controls changed')
            return done
        rows=[];all_sources=set(original_sources)
        for case in cases:
            earlier=case['source_worlds'][1:]
            # Never seed the intervention from the unit hash: it contains the
            # current work's unseen trajectory. Earlier source labels suffice.
            control_key=digest({'namespace':key,'earlier_lids':[w['lid'] for w in earlier]})
            row=units.get(case['unit'])
            if row is None:
                row={'unit':case['unit'],'control':construct(earlier,role,control_key)}
                units.put(case['unit'],row)
            validate(earlier,row['control'],role,control_key)
            if any(s in all_sources for s in row['control']['sources']):
                raise ValueError('control sources overlap another independent source unit')
            all_sources.update(row['control']['sources']);rows.append(row)
        freeze(directory/'CONTROLS.json',rows);verify_sources(source)
        done={'at':datetime.now(timezone.utc).isoformat(),'identity_sha256':digest(identity),'cell_identity':cell,
              'source':source,'role':role,'accepted':True,'execution_complete':True,'assigned_units':len(cases),
              'completed_units':len(rows),'control_worlds':sum(len(r['control']['worlds']) for r in rows),
              'matching':'exact public initial conditions, inventory and per-work purpose; different persistent maker',
              'unmatched':['realized trajectory length','realized marks','per-work belief as part of the alternative maker'],
              'target_work_read_by_control_constructor':False,'scored_predictions':False,
              'outputs':closure([directory/'CONTROLS.json',directory/'units']),
              'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,'gpu_seconds':0}
        freeze(directory/'COMPLETE.json',done);return done


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','cases','role','key'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();run(Path(args.root),Path(args.cases),role=args.role,key=args.key)
    print('Matched public-condition controls complete; no prospective scores computed.',flush=True)


if __name__=='__main__':main()
