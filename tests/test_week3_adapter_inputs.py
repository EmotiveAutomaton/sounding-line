"""WA1 preserves every saved case and authenticates canonical label changes."""
import copy
import json
import pytest

from runners.drive.cards import week3_adapter_inputs as card

def fixture():
    cases={};costs={};predictions=[];calibration={}
    for w in ['a','b']:
        phases={}
        for phase in ['calibration','evaluation']:
            phases[phase]=[dict(key=f'{w}-{phase}-{i}',writer=w,prompt='p'+str(i),truth=0,
                canonical_truth=i,lengths=[2,3],session=f'{w}-{phase}',ordinal=i,input_digest='fixed') for i in range(2)]
        cases[w]=phases;details={};calibration[w]={}
        for arm in card.ARMS:
            raw=[[-1.,-4.],[-2.,-5.]];temp=card.temperature(raw,phases['calibration'])
            details[arm]=dict(calibration_raw=raw,evaluation_raw=raw)
            calibration[w][arm+'_mean']=dict(temperature=temp,calibration_cases=2)
        for i,r in enumerate(phases['evaluation']):
            predictions.append({k:r[k] for k in ['key','writer','prompt','truth']}|dict(probabilities={
                arm+'_mean':card.normalized(details[arm]['evaluation_raw'][i],r['lengths'],calibration[w][arm+'_mean']['temperature'])
                for arm in card.ARMS}))
        costs[w]=dict(details=details,donor='b' if w=='a' else 'a',cutoff=10.)
    return dict(name='fixture',cases=cases,costs=costs,predictions=predictions,calibration=calibration)

def test_saved_likelihoods_bind_every_old_and_corrected_case():
    f=fixture();r=card.prepare_cell(**f)
    assert r['census']==dict(calibration_rows=4,calibration_changed=2,evaluation_rows=4,evaluation_changed=2)
    assert [w['writer'] for w in r['writers']]==['a','b']
    assert r['writers'][0]['cases']['evaluation'][1]['canonical_truth']==1
    assert r['writers'][0]['raw']['base']['calibration']==f['costs']['a']['details']['base']['calibration_raw']

@pytest.mark.parametrize('defect',['missing','extra','raw','temperature'])
def test_corrupt_saved_population_or_probability_refuses(defect):
    f=fixture()
    if defect=='missing':f['predictions'].pop()
    if defect=='extra':f['predictions'].append(dict(f['predictions'][0],key='not-a-saved-key'))
    if defect=='raw':f['costs']['a']['details']['base']['evaluation_raw'][0]=[0.,0.]
    if defect=='temperature':f['calibration']['a']['base_mean']['temperature']=9.
    with pytest.raises(ValueError):card.prepare_cell(**f)

def test_canonical_choice_uses_verified_position_not_logged_index():
    c=dict(key='k',writer='w',prompt='p',truth=0,choices=[[1,2],[3]],input_digest='x')
    r=dict(writer='w',session='s',ordinal=3,option_indices=[5,8]);t=dict(selected_index=5)
    proof=dict(writer='w',session='s',ordinal=3,canonical_option_ids=[5,8],canonical_usable=True,
        verified_insertion=True,canonical_handling='edit',canonical_positions=[1],logged_selected_index=5,
        raw_source_sha256='r',canonical_sha256='c')
    actual=card.canonical_case(c,r,t,{'k':proof},{'s':dict(source_sha256='r')})
    assert actual['truth']==0 and actual['canonical_truth']==1 and actual['lengths']==[2,1]
    for change in [dict(canonical_positions=[0,1]),dict(canonical_option_ids=[8,5]),dict(verified_insertion=False)]:
        with pytest.raises(ValueError):card.canonical_case(c,r,t,{'k':proof|change},{'s':dict(source_sha256='r')})

def test_token_lengths_and_raw_support_are_validated():
    for lengths in [[1.5,2],[True,2],[0,2],[2]]:
        with pytest.raises(ValueError):card.normalized([-1.,-2.],lengths,1.)
    with pytest.raises(ValueError):card.normalized([float('nan'),1.],[2,2],1.)

def test_complete_constructed_execute_verify_and_source_mutation(tmp_path):
    source=tmp_path/'fixture.json';source.write_text(json.dumps(fixture()),encoding='utf8')
    inputs=dict(fixture=str(source));out=tmp_path/'output'
    assert card.execute(out,inputs,card.CONSTRUCTED)['no_new_inference']
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    source.write_text(source.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)
