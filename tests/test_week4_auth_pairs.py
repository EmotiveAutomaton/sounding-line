import copy
import pytest
from runners.drive.cards import week4_auth_pairs as a


def test_fixture_exact_matching_balance_and_order():
    data=a.fixture();c=a.configuration('constructed');rows,sel,s=a.draw(data,c)
    assert s['pairs']==96 and s['writers']==4 and s['duplicate_pairs']==0
    assert a.draw(list(reversed(data)),c)==(rows,sel,s)
    assert len(sel['calibration'])==len(sel['fresh'])==8 and not set(sel['calibration'])&set(sel['fresh'])
    assert sum(r['same_writer'] for r in rows if r['pair_id'] in sel['calibration'])==4
    assert all(r['genre']=='argumentative' for r in rows if r['pair_id'] in sel['calibration']+sel['fresh'])


def test_unavailable_support_refused():
    data=a.fixture();c=a.configuration('constructed')
    for r in data:r['prompt']='same'
    with pytest.raises(ValueError):a.draw(data,c)
    data=a.fixture();data[0]['typed']['text']=data[1]['typed']['text']
    with pytest.raises(ValueError):a.draw(data,c)
    data=a.fixture();data[0]['source_exact']=False
    with pytest.raises(ValueError):a.draw(data,c)


@pytest.mark.parametrize('change',['truth','text','prompt','duplicate','missing'])
def test_independent_pair_validator_catches_changes(change):
    data=a.fixture();c=a.configuration('constructed');rows,_,_=a.draw(data,c)
    if change=='truth':rows[0]['same_writer']=False
    if change=='text':rows[0]['texts'][0]='forged'
    if change=='prompt':rows[0]['prompts'][0]='forged'
    if change=='duplicate':rows[1]=copy.deepcopy(rows[0])
    if change=='missing':rows.pop()
    with pytest.raises(ValueError):a.validate(rows,data,c)


def test_complete_handlers_and_source_refusal(tmp_path):
    c=a.configuration('constructed');a.execute(tmp_path,{},c)
    assert a.verify(tmp_path,{},c)['independent_identity_prompt_checks']
    with pytest.raises(ValueError):a.load({})
    with pytest.raises(ValueError):a.execute(tmp_path,{'hidden':'source'},c)
    (tmp_path/'PROVIDER_TEXTS.json').write_text('[]',encoding='utf8')
    with pytest.raises(ValueError):a.verify(tmp_path,{},c)
