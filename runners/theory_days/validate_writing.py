"""Literal TD7 source-handler rehearsal, with a nonempty known support case.

DESIGN CHECK: LESSONS 2-5. Twenty writers with ten matched disjoint windows
pass the source floor exactly; nineteen fail. Neither result is an effect.
"""
from pathlib import Path
import gzip,json
from runners.stage14.common import freeze,read,filehash
from . import writing_support as w


def fixture(writers=20):
    sessions=[];nav=[]
    for writer in range(writers):
        for sid in range(20):
            start=sid*1000;key=f'constructed-{writer}-{sid}';menus=[]
            for j in range(4):
                handling='dismiss' if sid%2==0 and j==0 else 'accept'
                m=dict(key=f'{key}-{j}',session=key,writer=f'w{writer}',ordinal=j,
                    open_at=start+j*10,resolved_at=start+j*10+1,
                    handling=handling,choice=2 if handling=='dismiss' else 0)
                menus.append(m);nav.append(dict(key=m['key'],session=key,writer=m['writer'],
                    canonical_choice=m['choice'],navigation=dict(hover_ordinals=[j])))
            sessions.append(dict(session=key,timestamp=start,end_at=start+100,menus=menus))
    return sessions,nav


def execute(output,inputs,config):
    output=Path(output);sessions,nav=fixture();actual={}
    for name,rows,filename in [('menus',sessions,'MENUS.json.gz'),('hover',nav,'PRIVATE_ROWS.json.gz')]:
        root=output/name;p=root/'output'/filename;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('wb') as f:
            with gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z:z.write(json.dumps(rows,sort_keys=True).encode())
        freeze(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
               outputs={'output/'+filename:filehash(p)}))
        actual[name+'_completion']=str(root/'COMPLETE.json')
    w.execute(output/'consumer',actual,{})
    s=read(output/'consumer/SUMMARY.json')
    assert s['support_pass'] and s['matched_pairs']==200 and s['writers_with_ten_pairs']==20
    assert not w.support(*fixture(19))[0]['support_pass']
    freeze(output/'FIXTURE_INPUTS.json',actual)
    return dict(constructed=True,actual_handler_executed=True)


def verify(output,inputs,config):
    output=Path(output);w.verify(output/'consumer',read(output/'FIXTURE_INPUTS.json'),{})
    return dict(verified=True,complete_handler_replay=True,constructed=True)
