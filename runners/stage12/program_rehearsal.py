"""Zero-inference exhaustive request/analysis rehearsal; never scientific evidence.

DESIGN CHECK: LESSONS 3-5. NULL: empty or incomplete rosters fail; exact known
targets have zero excess loss and invalid outputs retain their penalty.
ALTERNATIVE: every frozen slot, branch, label inverse and whole-family consumer
replays with synthetic replies. This does not admit a model or source theory.
"""
import argparse
import json
from pathlib import Path
from .common import REPO,read,freeze,filehash,digest
from .program_prepare import PROGRAM,ORDER
from . import program as P


def run(raw,scratch):
    scratch=Path(scratch);counts={};reports={}
    for family in ORDER:
        specs=read(Path(raw)/'inputs'/(family+'.json'));rows=[];bodies={}
        for spec in specs:
            r,req=P.effective(spec,rows,bodies)
            p=[r['target'][i] for i in r['label_order']]
            value=dict(probabilities=p,wall_seconds=0.)
            result=P.score(r,value)
            if abs(result['excess_half_brier'])>1e-12:raise ValueError('known exact forecast fails ruler')
            bodies[r['id']]=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='FAKE TRANSPORT ONLY',probabilities=p))))
            rows.append(result)
        root=scratch/'jobs'/family;freeze(root/'ROWS.json',rows)
        freeze(root/'COMPLETE.json',dict(status='complete',output_files={'ROWS.json':filehash(root/'ROWS.json')}))
        report=P.consume(scratch/'analysis'/family,dict(family=family,source_jobs=[family],calls=len(rows)),lambda **kw:None,scratch)
        counts[family]=len(rows);reports[family]=digest(report)
        print(family,len(rows),'all slots and analysis verified',flush=True)
    result=dict(status='complete',fake_only=True,calls=sum(counts.values()),counts=counts,analysis_digests=reports,no_inference=True)
    freeze(scratch/'REHEARSAL.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=PROGRAM);p.add_argument('--scratch',required=True,type=Path);a=p.parse_args();print(run(a.raw,a.scratch))
