"""Exact WB1 conditional references split into independently verified blocks."""
from pathlib import Path
from collections import Counter
import time
import numpy as np
from runners.stage14.common import read,filehash,digest,atomic
from . import week5_bk_wb1_source as source
from . import week3_pieces_stats as stats
from . import week3_pieces_effects_h1_pilot as pilot
from .timing_p6 import gzread,gzip_equal,write_equal


def materials(inputs,scope):
    root,manifest,rows=source.load(inputs['source_root'])
    if scope not in ('whole','thirds'):raise ValueError('Unknown unchanged null scope')
    cfg=manifest['config']
    candidate=stats.candidates([r for r in rows if r['side']=='discovery'],cfg['minimum_occurrences'],cfg['minimum_writers'])
    binding=digest(dict(source=manifest['binding'],scope=scope,draws=200,seed=stats.SEED,
                        statistic_sha256=filehash(stats.__file__)))
    return manifest,rows,candidate,binding


def discovery(path,source_root,scope):
    root,plan=source.completed(path,__name__)
    if plan['config']!={'operation':'discovery_reduce','scope':scope} or plan['inputs']['source_root']!=source_root:
        raise ValueError('Discovery depends on another source or scope')
    result=read(root/'output/DISCOVERY.json')
    _,_,candidate,binding=materials(dict(source_root=source_root),scope)
    if result['binding']!=binding or result['reference_draws']!=200 or result['candidates']!=len(candidate):
        raise ValueError('Incomplete or changed discovery')
    return result


def reference(rows,candidate,pieces,scope,side,draw):
    if side=='discovery':
        counts=Counter()
        for row in rows:
            if row['side']!='discovery':continue
            sequence=stats.surrogate(row['symbols'],row['seconds'],row['duration'],stats.derived_seed(scope,draw,row['session']),scope=='thirds')
            counts.update(piece for piece in stats.ngrams(sequence) if piece in candidate)
        return [counts[key] for key in sorted(candidate)]
    values=[]
    for row in rows:
        if row['side']!='test':continue
        sequence=stats.surrogate(row['symbols'],row['seconds'],row['duration'],stats.derived_seed(scope,draw,row['session']),scope=='thirds')
        values.append(stats.greedy_cover(sequence,pieces)[0])
    return values


def collected(paths,inputs,scope,side,binding):
    records={}
    for path in paths:
        root,plan=source.completed(path,__name__);cfg=plan['config']
        if plan['inputs']!=inputs or cfg.get('operation')!='reference_block' or cfg.get('scope')!=scope or cfg.get('side')!=side:
            raise ValueError('Reference block used a different source or scope')
        block=read(root/'output/BLOCK.json')
        if block['binding']!=binding or [r['draw'] for r in block['records']]!=list(range(cfg['start'],cfg['start']+cfg['count'])):
            raise ValueError('Reference block binding or global range changed')
        for record in block['records']:
            if record['draw'] in records:raise ValueError('Duplicate reference index')
            records[record['draw']]=record['values']
    if set(records)!=set(range(200)):raise ValueError('All original 200 references required')
    return [records[i] for i in range(200)]


def component(rows,candidate,discovered,bank,scope):
    pieces=discovered['pieces'];primary=[p['symbols'] for p in pieces if p['primary_eligible']]
    test=[r for r in rows if r['side']=='test']
    if any(len(value)!=len(test) for value in bank):raise ValueError('Reference writer/session denominator changed')
    null=np.zeros(len(test),float)
    for values in bank:null+=np.asarray(values,float)
    null/=200
    real=[stats.greedy_cover(r['symbols'],primary) for r in test]
    covered=[dict(session=r['session'],writer=r['writer'],events=len(r['symbols']),real_covered=a[0],reference_covered=float(b)) for r,a,b in zip(test,real,null)]
    all_pieces={tuple(p['symbols']) for p in pieces}
    occurrences=[o for row in rows for o in pilot.occurrences(row,all_pieces)]
    return dict(scope=scope,candidates=len(candidate),pieces=pieces,primary_pieces=len(primary),
                coverage=stats.coverage_interval(covered,2000,stats.SEED),writer_disjoint=True,
                reference_draws=200,rows=covered,occurrences=occurrences)


def run(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True);operation=config.get('operation')
    if operation=='coverage_reduce':
        required={'source_root','whole_discovery','thirds_discovery','whole_blocks','thirds_blocks'}
        if set(inputs)!=required or set(config)!={'operation'}:raise ValueError('Exact full coverage bank required')
        scopes={};manifest=None
        for scope in ('whole','thirds'):
            manifest,rows,candidate,binding=materials(inputs,scope)
            discovered=discovery(inputs[scope+'_discovery'],inputs['source_root'],scope)
            test_inputs=dict(source_root=inputs['source_root'],discovery_root=inputs[scope+'_discovery'])
            bank=collected(read(inputs[scope+'_blocks']),test_inputs,scope,'test',digest(dict(source=binding,pieces=discovered['pieces'])))
            scopes[scope]=component(rows,candidate,discovered,bank,scope)
        coarse=manifest['config']['coarse']
        result=dict(card='WB1b-coverage' if coarse else 'WB1-coverage',status='component_complete',scientific_admission=False,
                    full_card_complete=False,whole=scopes['whole'],thirds=scopes['thirds'],
                    route=stats.route(scopes['whole']['coverage'],scopes['thirds']['coverage'],scopes['whole']['primary_pieces'],coarse),
                    effects_and_classes='required separate source-replayed consumer; no downstream launch licensed by this receipt alone')
        source.checked(root/'WB1_COVERAGE_RESULT.json',result,verifying)
        # The original unsupported primary is retained; pooled counts are a separate fallback.
        fallback={}
        for scope,value in scopes.items():
            if value['coverage']['state']=='unsupported':
                total=sum(r['events'] for r in value['rows'])
                fallback[scope]=dict(state='below floor, descriptive',events=total,
                    coverage_difference=sum(r['real_covered']-r['reference_covered'] for r in value['rows'])/total if total else None,
                    interval=None,scope='pooled held-out event counts; no writer-population interval')
        source.checked(root/'DESCRIPTIVE_FALLBACK.json',fallback,verifying)
    elif operation=='discovery_reduce':
        if set(inputs)!={'source_root','blocks'} or set(config)!={'operation','scope'}:raise ValueError('Exact discovery bank required')
        scope=config['scope'];manifest,rows,candidate,binding=materials(inputs,scope)
        bank=collected(read(inputs['blocks']),dict(source_root=inputs['source_root']),scope,'discovery',binding)
        keys=sorted(candidate)
        if any(len(value)!=len(keys) for value in bank):raise ValueError('Candidate dimension changed')
        references={key:[value[j] for value in bank] for j,key in enumerate(keys)}
        result=dict(binding=binding,scope=scope,candidates=len(keys),reference_draws=200,pieces=stats.discover(candidate,references))
        source.checked(root/'DISCOVERY.json',result,verifying)
    elif operation=='reference_block':
        if set(config)!={'operation','scope','side','start','count'} or config['side'] not in ('discovery','test'):
            raise ValueError('Exact reference block contract required')
        side=config['side'];scope=config['scope'];start=config['start'];count=config['count']
        if type(start) is not int or type(count) is not int or not 0<=start<200 or not 1<=count<=10 or start+count>200:
            raise ValueError('Bounded original global reference indices required')
        if set(inputs)!={'source_root'}|({'discovery_root'} if side=='test' else set()):raise ValueError('Wrong reference dependencies')
        manifest,rows,candidate,binding=materials(inputs,scope);pieces=[]
        if side=='test':
            found=discovery(inputs['discovery_root'],inputs['source_root'],scope)
            pieces=[p['symbols'] for p in found['pieces'] if p['primary_eligible']]
            binding=digest(dict(source=binding,pieces=found['pieces']))
        records=[];began=time.monotonic()
        for draw in range(start,start+count):
            if (root/'YIELD_REQUEST.json').exists() or time.monotonic()-began>=1200:
                return dict(status='yielded',reason='sealed full conditional-reference boundary')
            path=root/f'draw-{draw:03d}.json';seal=root/f'draw-{draw:03d}.seal.json'
            if path.exists() and seal.exists() and not verifying:
                record=read(path)
                if read(seal)!={'sha256':filehash(path)} or record['binding']!=binding or record['draw']!=draw:
                    raise ValueError('Reference checkpoint binding or bytes changed')
            else:
                record=dict(binding=binding,draw=draw,values=reference(rows,candidate,pieces,scope,side,draw))
                source.checked(path,record,verifying);source.checked(seal,dict(sha256=filehash(path)),verifying)
            records.append(record)
            atomic(root/'PROGRESS.json',dict(phase='verify' if verifying else 'reference',completed=len(records),count=count,global_draw=draw))
        source.checked(root/'BLOCK.json',dict(binding=binding,records=records),verifying)
    else:raise ValueError('Unknown WB1 coverage operation')
    return dict(verified=True,full_original_reference_replay=True) if verifying else dict(status='complete',operation=operation,scientific_admission=False)


def execute(output,inputs,config):return source.timed(run,output,inputs,config,False)
def verify(output,inputs,config):return source.timed(run,output,inputs,config,True)
