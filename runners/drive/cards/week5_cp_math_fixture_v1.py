"""Independent CP1 known-answer worlds; authored counts, never human data.

The orthogonal four-row pattern gives observed complementary correlation
1/sqrt(626), no assertion matching, and perfect warmth matching. Swapping the
two reply columns reverses the primary exactly. The 200-shuffle correction is
checked against direct raw-row centered products, not the moment implementation.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
from . import week5_cp_statistics_v1 as stats
from . import week5_cp_analysis_v1 as analysis
from . import week5_rf_cp_fixture_v1 as intake_fixture
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_instrument_v1 as gate


def worlds(n=80,kind='complementary'):
    if kind not in ('complementary','convergent','identical'):raise ValueError('Unknown constructed world')
    result=[]
    for i in range(n):
        rows=[]
        for j,(x,z,w) in enumerate(((-1,-1,1),(-1,1,-1),(1,-1,-1),(1,1,1))):
            d=(250+x+25*z)/10;a=(250+25*w)/10
            if kind=='convergent':d,a=a,d
            if kind=='identical':a=d
            rows.append({'id':f'constructed-{i}-{j}','parent_assertion':(100+50*x)/10,
                'parent_warmth':(100+20*z)/10,'reply_deference':d,'reply_assertion':a,
                'reply_warmth':(100+20*z)/10,'parent_edit_count':10000+100*i+70*j,
                'reply_edit_count':8000+200*i+150*j+30*x*z})
        result.append((f'constructed-conversation-{i:03d}',rows))
    return result


def raw_correlation(x,y):
    n=len(x);mx=math.fsum(x)/n;my=math.fsum(y)/n
    xx=math.fsum((a-mx)**2 for a in x);yy=math.fsum((a-my)**2 for a in y)
    if xx<=0 or yy<=0:return None
    return math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(xx*yy)


def direct_primary(groups,draw=None,view='all'):
    copies=[1]*len(groups) if draw is None else stats.draw_counts(len(groups),draw,view).astype(int)
    values=[]
    for iteration in range(201):
        x=[];d=[];a=[]
        for count,(key,rows) in zip(copies,groups):
            order=range(len(rows)) if iteration==0 else stats.permutation(len(rows),key,iteration-1,view)
            for _ in range(count):
                for parent,j in zip(rows,order):
                    x.append(parent['parent_assertion']);d.append(rows[j]['reply_deference']);a.append(rows[j]['reply_assertion'])
        bd=raw_correlation(x,d);ba=raw_correlation(x,a)
        values.append(None if bd is None or ba is None else bd-ba)
    return None if any(v is None for v in values) else values[0]-math.fsum(values[1:])/200


def banks(groups,view='all'):
    return np.stack([stats.conversation_bank(stats.pair_array(rows),key,view) for key,rows in groups])


def mathematical_receipt(full_draws=True,check=None):
    receipts={};indexed=[]
    for kind in ('complementary','convergent','identical'):
        if check:check()
        groups=worlds(kind=kind);bank=banks(groups);total=np.sum(bank,axis=0)
        point=stats.evaluate(total);reference=stats.evaluate_reference(total)
        analysis.compare_metrics(point,reference)
        direct=direct_primary(groups)
        if abs(point['primary']-direct)>2e-10:raise ValueError('Direct row permutation oracle differs')
        observed=point['observed']
        expected=1/math.sqrt(626)
        if kind=='complementary' and (abs(observed['assertion_to_deference']-expected)>1e-10 or abs(observed['assertion_to_assertion'])>1e-10):
            raise ValueError('Literal orthogonal plant size failed')
        if abs(observed['warmth_to_warmth']-1)>1e-10:raise ValueError('Literal warmth answer failed')
        draws=[]
        for index in range(stats.BOOTSTRAPS if full_draws else 0):
            if check:check()
            total=np.einsum('c,crk->rk',stats.draw_counts(len(groups),index),bank,optimize=False)
            value=stats.evaluate(total);draws.append(value)
            if index in (0,999,1999):
                oracle=direct_primary(groups,index)
                if abs(value['primary']-oracle)>2e-10:raise ValueError('Whole-conversation draw oracle differs')
        receipts[kind]={'point':point,'uncertainty':stats.uncertainty(point,draws),
            'all_global_indices':list(range(len(draws))),'direct_primary':direct}
        indexed.append([d['primary'] for d in draws])
    if abs(receipts['complementary']['point']['primary']+receipts['convergent']['point']['primary'])>1e-12:
        raise ValueError('Complementary/convergent reversal failed')
    if receipts['identical']['point']['primary']!=0:raise ValueError('Exact paired null failed')
    if full_draws:
        if not np.allclose(indexed[0],-np.array(indexed[1]),atol=1e-12,rtol=0):raise ValueError('Global paired bootstrap reversal failed')
        if any(indexed[2]):raise ValueError('Exact paired bootstrap null failed')
        if receipts['complementary']['uncertainty']['primary']['interval'][0]<=.02:raise ValueError('Complementarity plant fails its practical bar')
        if receipts['convergent']['uncertainty']['primary']['interval'][1]>=-.02:raise ValueError('Convergence plant fails its practical bar')
    return {'by_construction':True,'worlds':receipts,'real_source_used':False,'scientific_admission':False}


def prepare_boundary(root):
    """Actual source/gate handlers inside explicit synthetic native envelopes."""
    root=Path(root);archive,salt,n=intake_fixture.prepare(root/'constructed-source','CP1',repeat=20)
    src_inputs={'archive':str(archive),'identity_salt':str(salt)}
    src_cfg={'family':'CP1','constructed_fixture':True,'fixture_archive_sha256':source.sha(archive),'fixture_expected_records':n}
    source.execute(root/'source-output',src_inputs,src_cfg)
    if source.verify(root/'source-output',src_inputs,src_cfg)['verified'] is not True:raise ValueError('Constructed source replay failed')
    inputs,cfg=intake_fixture.constructed_native_receipt(root/'source-native',root/'source-output')
    native=root/'instrument-native';native.mkdir(parents=True)
    gate.execute(native/'output',inputs,cfg)
    proof=gate.verify(native/'output',inputs,cfg)
    source.write_equal(native/'PLAN.json',{'module':'runners.drive.cards.week5_rf_cp_instrument_v1','constructed_fixture':True})
    source.write_equal(native/'VERIFIED.json',proof)
    names=('PLAN.json','VERIFIED.json','output/INSTRUMENT.json')
    source.write_equal(native/'COMPLETE.json',{'status':'COMPLETE','fresh_process_verified':True,'constructed_fixture':True,
        'outputs':{name:source.sha(native/name) for name in names}})
    inputs['instrument_native_root']=str(native)
    cfg.update(view='all',instrument_native_complete_sha256=source.sha(native/'COMPLETE.json'))
    return inputs,cfg


def execute(output,inputs,config):
    if inputs:raise ValueError('Constructed fixture takes no real source inputs')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);state=root/'FIXTURE_INPUTS.json'
    if not state.exists():
        prepared,cfg=prepare_boundary(root/'fixture-boundary')
        source.write_equal(state,{'inputs':prepared,'config':cfg})
    data=json.loads(state.read_text('utf8'))
    produced=analysis.execute(root/'handler',data['inputs'],data['config'])
    if produced['status']=='yielded':return produced
    replay=analysis.verify(root/'handler',data['inputs'],data['config'])
    if replay.get('verified') is not True:return dict(replay,status='yielded')
    try:receipt=mathematical_receipt(full_draws=True,check=lambda:analysis.check_yield(root))
    except analysis.YieldRequested:return {'status':'yielded','reason':'constructed_math_guard','by_construction':True}
    source.write_equal(root/'MATH_FIXTURE.json',receipt)
    source.write_equal(root/'FIXTURE_COMPLETE.json',{'by_construction':True,'real_source_used':False,
        'actual_source_gate_and_analysis_handlers':True,'fresh_handler_replay':replay,
        'math_fixture_sha256':source.sha(root/'MATH_FIXTURE.json'),'scientific_admission':False})
    return {'status':'complete','by_construction':True}


def verify(output,inputs,config):
    if inputs:raise ValueError('Constructed fixture takes no real source inputs')
    output=Path(output);original=json.loads((output/'MATH_FIXTURE.json').read_text('utf8'))
    try:repeated=mathematical_receipt(full_draws=True,check=lambda:analysis.check_yield(output))
    except analysis.YieldRequested:return {'verified':False,'status':'yielded','reason':'constructed_math_guard','by_construction':True}
    if source.canonical(original)!=source.canonical(repeated):raise ValueError('Constructed mathematical full replay differs')
    data=json.loads((output/'FIXTURE_INPUTS.json').read_text('utf8'))
    proof=analysis.verify(output/'handler',data['inputs'],data['config'])
    if proof.get('verified') is not True:return dict(proof,status='yielded')
    return {'verified':True,'full_three_world_2000_draws_replayed':True,'actual_source_and_consumer_replayed':True,
        'by_construction':True,'real_source_used':False,'scientific_admission':False}
