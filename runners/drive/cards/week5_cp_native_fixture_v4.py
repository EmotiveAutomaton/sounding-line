"""Counted CP1 fixture boundary: formal replay is reserved for native verify.

The statistical kernel remains V2; consumer V3 adds the joint source-case guard.
Earlier fixtures remain preserved. Formal replay is never created by execute.
"""
from pathlib import Path
import json
from . import week5_cp_analysis_v3 as analysis
from . import week5_cp_math_fixture_v3 as fixture
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_instrument_v1 as gate


def read(path):return json.loads(Path(path).read_text('utf8'))


def role_fixture():
    rows={}
    for parent_admin,reply_admin in ((False,False),(False,True),(True,False),(True,True)):
        role=f'{int(parent_admin)}{int(reply_admin)}'
        for side,admin in (('p',parent_admin),('r',reply_admin)):
            key=side+role
            rows[key]={'id':key,'speaker':side+role,'conversation':'constructed-'+role,
                'reply_to':None if side=='p' else 'p'+role,'is_admin':admin,'edit_count':100,
                'markers':{'tokens':10,'counts':{'assertion':3,'deference':2,'warmth':1}}}
    for role in ('00','01','10','11'):
        groups,support=analysis.pairs_from_rows(rows,'admin-'+role)
        if len(groups)!=1 or [r['id'] for r in groups[0][1]]!=['r'+role] or support['below_floor'] is not True:
            raise ValueError('Literal admin-role grid membership failed')
    groups,support=analysis.pairs_from_rows(rows,'all')
    if len(groups)!=4 or support['counts']['eligible_pairs']!=4:raise ValueError('Literal pooled role membership failed')
    return {'all_four_role_memberships_checked':True,'pooled_pairs':4,'below_floor_fallback_checked':True}


def execute(output,inputs,config):
    if inputs:raise ValueError('Constructed fixture takes no real source inputs')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    state=output/'FIXTURE_INPUTS.json'
    try:
        analysis.check_yield(output)
        if not state.exists():
            prepared,cfg=fixture.prepare_boundary(output/'fixture-boundary')
            origin=output/'fixture-boundary'/'constructed-source'
            archive=origin/'constructed-wiki.zip';salt=origin/'constructed-salt.bin'
            source.write_equal(state,{'inputs':prepared,'config':cfg,
                'source_inputs':{'archive':str(archive),'identity_salt':str(salt)},
                'source_config':{'family':'CP1','constructed_fixture':True,
                    'fixture_archive_sha256':source.sha(archive),'fixture_expected_records':400}})
        data=read(state)
        result=analysis.execute(output/'handler',data['inputs'],data['config'])
        if result['status']=='yielded':return result
        roles=role_fixture()
        receipt=fixture.mathematical_receipt(full_draws=True,check=lambda:analysis.check_yield(output))
        source.write_equal(output/'MATH_FIXTURE.json',receipt)
        source.write_equal(output/'FIXTURE_EXECUTE_COMPLETE.json',{
            'by_construction':True,'real_source_used':False,'scientific_admission':False,
            'statistical_consumer_sha256':source.sha(analysis.__file__),
            'math_fixture_sha256':source.sha(output/'MATH_FIXTURE.json'),
            'formal_handler_replay_run_by_execute':False,'role_grid_fixture':roles})
        return {'status':'complete','by_construction':True,'formal_native_verify_pending':True}
    except analysis.YieldRequested:return {'status':'yielded','reason':'constructed_fixture_guard','by_construction':True}


def verify(output,inputs,config):
    if inputs:raise ValueError('Constructed fixture takes no real source inputs')
    output=Path(output);data=read(output/'FIXTURE_INPUTS.json')
    if not (output/'FIXTURE_EXECUTE_COMPLETE.json').exists():raise ValueError('Incomplete constructed fixture')
    try:
        analysis.check_yield(output)
        roles=role_fixture()
        fresh=output/'formal-source-replay'
        result=source.produce(fresh,data['source_inputs'],data['source_config'])
        if result.get('status')=='yielded':return dict(result,verified=False)
        original=Path(data['inputs']['source_native_root'])/'output'
        complete=read(original/'SOURCE_COMPLETE.json')
        for name in ('BINDING.json','SUMMARY.json','REVIEW_PRIVATE.json','ADJUDICATION_TEMPLATE.json','SOURCE_COMPLETE.json',*complete['blocks']):
            if source.sha(original/name)!=source.sha(fresh/name):raise ValueError('Formal native source replay differs')
        instrument=Path(data['inputs']['instrument_native_root'])/'output'
        if gate.verify(instrument,data['inputs'],data['config']).get('verified') is not True:
            raise ValueError('Formal manual-gate arithmetic differs')
        # This tree is first created in the native verifier, never in execute.
        proof=analysis.verify(output/'handler',data['inputs'],data['config'])
        if proof.get('verified') is not True:return dict(proof,status='yielded')
        repeat=fixture.mathematical_receipt(full_draws=True,check=lambda:analysis.check_yield(output))
        if source.canonical(repeat)!=source.canonical(read(output/'MATH_FIXTURE.json')):
            raise ValueError('Formal full mathematical replay differs')
        return {'verified':True,'by_construction':True,'real_source_used':False,'scientific_admission':False,
            'formal_source_and_marker_rows_replayed':True,'formal_manual_gate_arithmetic_replayed':True,
            'formal_full_handler_replay':proof,'three_full_2000_draw_worlds_replayed':True,'role_grid_fixture':roles}
    except analysis.YieldRequested:
        return {'status':'yielded','verified':False,'reason':'constructed_fixture_guard','by_construction':True}
