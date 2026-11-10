"""Counted first-five-percent complete WB1 coverage work measurement."""
from pathlib import Path
import time
from runners.stage14.common import read,digest,filehash,atomic
from . import week5_bk_wb1_scope as source
from . import week5_bk_wb1_coverage_scoped as coverage
from . import week3_pieces_stats as stats


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'source_root'} or config:raise ValueError('Exact complete source and fixed five-percent pilot required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);began=time.monotonic();proof=[]
    for scope in ('whole','thirds'):
        manifest,rows,candidate,binding=coverage.materials(inputs,scope)
        # All candidates bound the eventual primary-piece covering work and
        # cannot substitute for actual discovery or its held-out reference bank.
        pieces=[list(p) for p in sorted(candidate)]
        for side in ('discovery','test'):
            for draw in range(10):
                if (root/'YIELD_REQUEST.json').exists() or time.monotonic()-began>=1200:
                    return dict(status='yielded',reason='complete pilot conditional-reference boundary')
                name=f'{scope}-{side}-{draw:02d}.json';path=root/name
                identity=dict(binding=binding,scope=scope,side=side,draw=draw,candidate_superset=True)
                seal=root/(name+'.seal.json')
                if path.exists() and seal.exists() and not verifying:
                    value=read(path)
                    if read(seal)!={'sha256':filehash(path)} or any(value[k]!=v for k,v in identity.items()):
                        raise ValueError('Pilot reference binding or bytes changed')
                else:
                    value=dict(**identity,values=coverage.reference(rows,candidate,pieces,scope,side,draw))
                    source.checked(path,value,verifying);source.checked(seal,dict(sha256=filehash(path)),verifying)
                proof.append(dict(file=name,sha256=filehash(path)))
                atomic(root/'PROGRESS.json',dict(phase='verify' if verifying else 'pilot',complete_references=len(proof),total=40))
    neutral=[dict(session=r['session'],writer=r['writer'],events=len(r['symbols']),real_covered=0,reference_covered=0) for r in rows if r['side']=='test']
    bootstrap=[stats.coverage_interval(neutral,2000,stats.SEED) for _ in range(2)]
    result=dict(source_binding=manifest['binding'],reference_work=proof,bootstrap_digest=digest(bootstrap),
                references_per_scope_side=10,total_per_scope_side=200,work_fraction=.05,
                full_shaped_cluster_draws=2000,candidate_superset=True,scientific_admission=False)
    source.checked(root/'COVERAGE_PILOT.json',result,verifying)
    source.write_scope(root,manifest,verifying)
    return dict(verified=True,full_original_pilot_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return source.timed(run,output,inputs,config,False)
def verify(output,inputs,config):return source.timed(run,output,inputs,config,True)
