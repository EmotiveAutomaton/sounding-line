"""Known source membership and refusal fixtures for original-law discarded input."""
import copy
import pytest
from runners.stage9.common import digest
from runners.stage9.original_collection_pilot import original_pool,COUNTS,ASSIGNED


def fixture():
    examples=[];worlds={}
    for domain in COUNTS:
        for i in range(32):
            key=f'{domain}-{i}';prior=key+'-earlier'
            law='expert' if i<COUNTS[domain] else 'editor2'
            for name in (key,prior):worlds[name]={'state':{'names':{'law':law}},'evaluator_future':['untouched']}
            examples.append({'key':key,'lineages':[key,prior],'raw_record':{'domain':domain},'input_ids':[1,2],'labels':[1,2]})
    return {'candidate_examples':examples,'private_worlds':worlds,'split':'pilot','original_pool_sha256':'a'*64}


def test_complete_known_original_subset_and_assigned_half():
    pool=fixture();before=copy.deepcopy(pool);result=original_pool(pool);selection=result['original_law_selection']
    assert pool==before and len(result['candidate_examples'])==30 and len(result['private_worlds'])==60
    assert selection['parent_pool_sha256']==digest(pool) and selection['domain_counts']==COUNTS
    assert len(selection['excluded'])==34 and len(selection['assigned_keys'])==ASSIGNED
    assert all(r in pool['candidate_examples'] for r in result['candidate_examples'])
    assert all(result['private_worlds'][k]==pool['private_worlds'][k] for k in result['private_worlds'])
    counts={d:sum(k.startswith(d+'-') for k in selection['assigned_keys']) for d in COUNTS}
    assert counts=={'essay':8,'workshop_doc':7}
    result['candidate_examples'][0]['input_ids'].append(9)
    assert pool==before


@pytest.mark.parametrize('role',['training','discovery','reserve'])
def test_scientific_role_cannot_enter_discarded_selector(role):
    pool=fixture();pool['split']=role
    with pytest.raises(ValueError,match='discarded parent'):original_pool(pool)


@pytest.mark.parametrize('fault',['missing_earlier','duplicate_key','unknown_law','incomplete_lineage','wrong_domain','missing_law'])
def test_invalid_complete_source_refuses(fault):
    pool=fixture();row=pool['candidate_examples'][0]
    if fault=='missing_earlier':del pool['private_worlds'][row['lineages'][1]]
    elif fault=='duplicate_key':pool['candidate_examples'][-1]['key']=row['key']
    elif fault=='unknown_law':pool['private_worlds'][row['key']]['state']['names']['law']='unregistered'
    elif fault=='incomplete_lineage':row['lineages']=[]
    elif fault=='wrong_domain':row['raw_record']['domain']='unregistered'
    else:del pool['private_worlds'][row['key']]['state']['names']['law']
    with pytest.raises(ValueError,match='original-law'):original_pool(pool)


def test_secondary_earlier_work_prevents_original_claim():
    pool=fixture();row=pool['candidate_examples'][0]
    pool['private_worlds'][row['lineages'][1]]['state']['names']['law']='editor2'
    with pytest.raises(ValueError,match='complete eligible domain counts'):original_pool(pool)


def test_changed_future_cannot_change_selection():
    pool=fixture();first=original_pool(pool);changed=copy.deepcopy(pool)
    for world in changed['private_worlds'].values():world['evaluator_future']=['different unknown outcome']
    second=original_pool(changed)
    assert first['original_law_selection']['selected_keys']==second['original_law_selection']['selected_keys']
    assert first['original_law_selection']['assigned_keys']==second['original_law_selection']['assigned_keys']
    assert first['original_law_selection']['parent_pool_sha256']!=second['original_law_selection']['parent_pool_sha256']


@pytest.mark.parametrize('family',['qwen','smollm'])
def test_actual_collector_boundary_accepts_original_only_as_discarded(tmp_path,monkeypatch,family):
    from runners.stage9 import scientific_collector as collector,training_jobs
    from runners.stage9.common import read,write,file_hash
    from runners.stage9.train import BASES
    parent=fixture();old={'examples':parent['candidate_examples'],'worlds':parent['private_worlds']}
    monkeypatch.setattr(collector,'ROOT',tmp_path)
    pool_dir=tmp_path/'private'/('pilot-dose/qwen' if family=='qwen' else 'pilot-dose-v3/smollm')
    write(pool_dir/'POOL.json',old)
    source=tmp_path/'discarded.json';write(source,{'identity':{'pool_sha256':digest(old)}})
    monkeypatch.setattr(training_jobs,'rehearsal_input',lambda _: (source,{}))
    training=tmp_path/'private/training-handler-pilots/v2'/family/'fit'
    fitted={'family':family,'base':BASES[family],'split':'pilot','seed':997901,'corpus_sha256':file_hash(source)}
    write(training/'IDENTITY.json',fitted);write(training/'COMPLETE.json',{'identity_sha256':digest(fitted)})
    write(training.parent/'COMPLETE.json',{'scope':'discarded-rehearsal','operation':'fit',
        'training_complete_sha256':file_hash(training/'COMPLETE.json')})
    _,_,pool,chosen=collector.collection_inputs(family,'original',training,rehearsal=True)
    assert len(pool['candidate_examples'])==30 and len(chosen)==15
    assert set(pool['original_law_selection']['assigned_keys'])==chosen
    assert pool['original_pool_sha256']==file_hash(pool_dir/'POOL.json')
    assert read(pool_dir/'POOL.json')==old
    assert len(collector.collection_inputs(family,'both',training,rehearsal=True)[3])==32
    with pytest.raises(ValueError,match='never a discarded pilot'):
        collector.collection_inputs(family,'original',training)
