"""Constructed IN9 cues, independent hand counts and complete actual handlers."""
from contextlib import contextmanager
from pathlib import Path
import copy
import math
import shutil
import pandas as pd
from . import week5_in9_cue_pipeline_v2 as study


@contextmanager
def source_boundary(base, extra, identity=None):
    before=study.load_source
    try:
        study.load_source=lambda inputs:(base.copy(),extra.copy(),identity or {'constructed':'source-v1'})
        yield
    finally: study.load_source=before


@contextmanager
def prepared_boundary(frame, audit_sample, audit, identity):
    before=study.load_prepared
    try:
        study.load_prepared=lambda inputs:(frame.copy(),copy.deepcopy(audit_sample),copy.deepcopy(audit),dict(identity))
        yield
    finally: study.load_prepared=before


def source_world():
    prompts=['shame','guilt','shame','guilt']
    texts=['She was angry at me; everyone saw. I hurt her.',
           'They laughed at me and mocked me in front of everyone.',
           'I forgot. I forgot. He yelled at me.', 'A quiet morning.']
    base=pd.DataFrame([{'text_id':f't{i}','prolific_id':f'p{i//2}','emotion':prompts[i]} for i in range(4)])
    extra=base.copy(); extra['generated_text']=texts
    return base,extra


def source_chain(output):
    output=Path(output); base,extra=source_world(); pilot=output/'pilot'; full=output/'full'
    config={'phase':'IN9-cues-prepare','draws':2000,'max_new_draws':1,'max_wall_seconds':100}
    with source_boundary(base,extra):
        assert study.execute(pilot,{},config)['status']=='yielded'
        pins={p.relative_to(pilot).as_posix():study.io.sha(p) for p in pilot.rglob('*') if p.is_file()}
        shutil.copytree(pilot,full)
        assert study.execute(full,{},dict(config,max_new_draws=10))['complete_preparation']
        assert study.verify(full,{},config)['verified'] is False
        assert study.verify(full,{},dict(config,max_new_draws=10))['verified'] is True
    expected=[(1,1,1,0),(0,2,0,2),(2,0,1,0),(0,0,0,0)]
    rows=study.seal.read(full/'TABLE.json')['rows']
    assert [tuple(row[n] for n in study.math.FAMILIES) for row in rows]==expected
    assert all(set(row)=={'text_id','prolific_id','emotion',*study.math.FAMILIES} for row in rows)
    assert all(study.io.sha(pilot/n)==h for n,h in pins.items())
    study.io.write_json(output/'FIXTURE.json',{'passed':True,'hand_count_rows':4,'immutable_source_reentry':True,
        'independent_full_count_replay':True,'no_text_written':True,'record_kind':'run','theory_tags':[],
        'by_construction':True,'activation':[]})
    return rows


def world(kind='null', writers=40):
    rows=[]
    for person in range(writers):
        for prompt in ('shame','guilt'):
            hits=(4+(person%3)-1) if kind=='null' else ((6+(person%3)-1) if prompt=='shame' else 3)
            for index in range(10):
                rows.append({'text_id':f'{person:04}-{prompt}-{index:02}','prolific_id':f'p{person:04}',
                    'emotion':prompt,**{name:int(index<hits) for name in study.math.FAMILIES}})
    return pd.DataFrame(rows).sort_values('text_id').reset_index(drop=True)


def reviews(frame):
    specimen=study.sample(frame.to_dict('records'))
    identity={'prepared_complete_sha256':'constructed-complete','table_sha256':study.digest(frame.to_dict('records')),
              'sample_sha256':study.digest(specimen),'source_identity':{'constructed':True}}
    audit={**{k:identity[k] for k in ('prepared_complete_sha256','table_sha256','sample_sha256')},
           'reviewer_role':'constructed known answers','method':'local blinded context review; no text exported',
           'families':{name:[{'text_id':key,'correct':True,'reason':'context_supports'} for key in s['private_text_ids']]
                       for name,s in specimen['families'].items()}}
    identity['audit_sha256']=study.digest(audit)
    return specimen,audit,identity


def full_chain(output, kind):
    output=Path(output); frame=world(kind); specimen,audit,identity=reviews(frame)
    small={'phase':'IN9-cues','draws':2000,'max_new_draws':100,'max_wall_seconds':150}
    full=dict(small,max_new_draws=2000); pilot=output/'pilot'; continued=output/'full'
    with prepared_boundary(frame,specimen,audit,identity):
        assert study.execute(pilot,{},small)['status']=='yielded'
        pins={p.relative_to(pilot).as_posix():study.io.sha(p) for p in pilot.rglob('*') if p.is_file()}
        shutil.copytree(pilot,continued)
        result=study.execute(continued,{},full)
        assert study.verify(continued,{},small)['verified'] is False
        assert study.verify(continued,{},full)['verified'] is True
    for name in study.math.FAMILIES:
        point=result['cues'][name]
        assert point['draws']==2000 and not point['failed_draws']
        if kind=='null':
            assert point['log_odds_ratio']==0 and point['odds_ratio']==1
            assert point['status']=='degenerate empirical uncertainty, descriptive'
        else:
            shame_hits=sum(6+(p%3)-1 for p in range(40)); guilt_hits=120
            expected=math.log((shame_hits/(400-shame_hits))/(guilt_hits/(400-guilt_hits)))
            assert abs(point['log_odds_ratio']-expected)<1e-12
            assert point['log_odds_interval'][0]>0
    assert all(study.io.sha(pilot/n)==h for n,h in pins.items())
    proof={'passed':True,'world':kind,'full_draws':2000,'all_four_families':True,
           'complete_independent_odds_replay':True,'immutable_source_and_verifier_reentry':True,
           'record_kind':'run','theory_tags':[],'by_construction':True,'activation':[]}
    study.io.write_json(output/'FIXTURE.json',proof);return proof
