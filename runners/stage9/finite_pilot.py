"""Actual finite-constructor operation fixture for compression and longer distinction.

DESIGN CHECK: I05/C04. Thirty-two discarded cases across both existing domains;
exact executor passes, constant reader misses distinctions, history-confounded
reader invents distinctions for equivalent histories. No neural competence verdict.
"""
from collections import Counter
from pathlib import Path
import time
from runners.stage9.common import REPO,ROOT,closure,digest,freeze,read
from runners.stage9.finite_world import case
from runners.stage9.automata import accepts,evaluate
from runners.stage9.recipes import POP


def run():
    output=ROOT/'private/pilot-finite-v1'
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    started=time.time();cases=[];excluded=Counter();attempted=Counter()
    for domain in POP.DOMAINS:
        kept=0
        for index in range(1600):
            attempted[domain]+=1
            try:c=case(index,domain)
            except ValueError as exc:
                excluded[str(exc)]+=1;continue
            cases.append(c);kept+=1
            if kept==16:break
        if kept!=16:raise ValueError('bounded finite-language case preparation exhausted')
    identity={'source':closure([REPO/'runners/stage9'/n for n in ('finite_pilot.py','finite_world.py','automata.py',
                'recipes.py','construction.py','common.py')]+[REPO/'runners/stage7/constructor',REPO/'runners/stage7/reader',
                REPO/'runners/stage8/constructor',REPO/'runners/stage8/reader/logfmt.py',REPO/'runners/stage8/engines.py']),
              'cases':len(cases),'band':9970000,'horizon':4,'alphabet':'three declared existing inventory actions times two outcomes plus STOP',
              'source_operation':'https://arxiv.org/html/2406.03689v3 Sections 2.3-2.4, definitions 2.4-2.6 read',
              'scope':'independently checked bounded-language operation adaptation; no reproduction of paper model results'}
    freeze(output/'IDENTITY.json',identity);freeze(output/'CASES.json',cases)
    records=[]
    for c in cases:
        d=c['distinction'];comp=c['compression'];a,b=d['left'],d['right'];g,h=comp['left'],comp['right']
        left=lambda s:accepts(a,a['initial'],s)
        right=lambda s:accepts(b,b['initial'],s)
        cl=lambda s:accepts(g,g['initial'],s)
        cr=lambda s:accepts(h,h['initial'],s)
        constant=lambda s:True
        # Right-only boundary is nonempty when the library arrives; keep direction
        # explicit instead of treating a directed relation as a symmetric one.
        exact=evaluate(right,left,right,left,a['alphabet'],4)
        blind=evaluate(right,left,constant,constant,a['alphabet'],4)
        compressed=evaluate(cl,cr,cl,cr,g['alphabet'],4)
        wrong_compression=evaluate(cl,cr,right,left,g['alphabet'],4)
        checks={'exact_distinction':exact['precision']==exact['recall']==1,
                'constant_distinction_fails':blind['recall']==0,
                'exact_compression':compressed['precision']==1 and compressed['true_boundary_size']==0,
                'invented_history_difference_fails':wrong_compression['precision']==0,
                'long_separator':len(d['separator']['suffix'])>=2 and d['one_step_support_identical']}
        records.append({'source_lineage':c['source_lineage'],'checks':checks,'exact_distinction':exact,
                        'constant_distinction':blind,'exact_compression':compressed,'wrong_compression':wrong_compression})
    if not all(all(r['checks'].values()) for r in records):raise ValueError('finite operation ruler failed its actual cases')
    freeze(output/'CHECKS.json',records)
    receipt={'identity_sha256':digest(identity),'attempted':dict(attempted),'excluded':dict(excluded),'completed_cases':len(records),
             'checks_passed':dict(Counter(k for r in records for k,v in r['checks'].items() if v)),
             'horizon':4,'minimum_separator_length':min(len(c['distinction']['separator']['suffix']) for c in cases),
             'wall_seconds':time.time()-started,'completed_at':time.time(),
             'neural_competence_evaluated':False,'scope':identity['scope']}
    freeze(output/'COMPLETE.json',receipt);freeze(ROOT/'pilot/FINITE_OPERATIONS.json',receipt)
    return receipt


if __name__=='__main__':print(run())
