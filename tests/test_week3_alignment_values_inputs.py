import copy
import gzip
import json

import pytest

from runners.drive.cards import week3_alignment_values_inputs as card,week3_values_inputs as val
from runners.stage14.common import digest,filehash,freeze,read,atomic
from tests.test_week3_values_inputs import fixture


def example():
    rows=[dict(writer='a',conversation='c'+str(i),turn=i,prompt='p'+str(i),half=i%2,country='X',
               explanation='' if i%2 else 'statement '+str(i)) for i in range(4)]
    rows += [dict(writer='b',conversation='c'+str(i),turn=i,prompt='p'+str(i),half=i%2,country='X',
                  explanation='statement b '+str(i)) for i in range(4)]
    sample,census=val.choice_sample(rows,['a','b']);items,joins=val.deduplicate(sample)
    return rows,items,joins


def test_explanation_comparisons_never_enter_choice_fit():
    rows,items,joins=example();result=card.partition(rows,['a','b'],items,joins)
    assert result[0]['fit_indices']==[1,3]
    assert [r['comparison_index'] for r in result[0]['targets']]==[0,2]
    assert result[1]['unsupported_reasons']==['no-comparisons-without-explanations']
    assert len(result)==2


def test_unsampled_explanation_is_excluded_too():
    rows,items,joins=example();remove=next(k for k,v in joins.items() if v[0]['writer']=='a')
    del joins[remove];items=[r for r in items if r['item_id']!=remove]
    result=card.partition(rows,['a','b'],items,joins)
    assert result[0]['fit_indices']==[1,3] and len(result[0]['targets'])==1


def test_changed_text_context_or_duplicate_target_refuses():
    rows,items,joins=example()
    damaged=copy.deepcopy(joins);first=next(iter(damaged));damaged[first][0]['prompt']='other'
    with pytest.raises(ValueError,match='context'):card.partition(rows,['a','b'],items,damaged)
    damaged=copy.deepcopy(joins);damaged[first].append(copy.deepcopy(damaged[first][0]))
    with pytest.raises(ValueError,match='duplicate'):card.partition(rows,['a','b'],items,damaged)
    items[0]['text']='changed'
    with pytest.raises(ValueError,match='semantic'):card.partition(rows,['a','b'],items,joins)


def fixture_chain(root):
    inputs=fixture(root/'sources')
    prepared=__import__('pathlib').Path(inputs['prepared_summary']).parent
    with gzip.open(prepared/'COMPARISONS.jsonl.gz','rt',encoding='utf8') as stream:rows=[json.loads(x) for x in stream]
    for row in rows:row['country']='X'
    # Leave five fit-only comparisons per person, preserving at least ten targets.
    for row in rows:
        if row['turn']>=15:row['explanation']=''
    with gzip.open(prepared/'COMPARISONS.jsonl.gz','wt',encoding='utf8') as stream:stream.writelines(json.dumps(r)+'\n' for r in rows)
    summary=read(prepared/'SUMMARY.json');summary['output_hashes']['COMPARISONS.jsonl.gz']=filehash(prepared/'COMPARISONS.jsonl.gz')
    atomic(prepared/'SUMMARY.json',summary)
    terminal=read(inputs['prepared_complete']);terminal['outputs']['output/SUMMARY.json']=filehash(prepared/'SUMMARY.json')
    atomic(inputs['prepared_complete'],terminal)
    out=root/'val-source/output';val.execute(out,inputs,{'fixture':True});val.verify(out,inputs,{'fixture':True})
    freeze(out.parent/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={'output/SUMMARY.json':filehash(out/'SUMMARY.json')}))
    return dict(prepared_summary=inputs['prepared_summary'],prepared_complete=inputs['prepared_complete'],
                values_input_summary=str(out/'SUMMARY.json'),values_input_complete=str(out.parent/'COMPLETE.json'))


def test_complete_source_chain_and_fresh_partition_replay(tmp_path):
    inputs=fixture_chain(tmp_path/'input');out=tmp_path/'out'
    summary=card.execute(out,inputs,{})
    assert summary['fixed_annotators']==30 and summary['fit_comparisons_without_explanations']==150
    assert summary['heldout_explanation_targets']==300 and summary['full_population_input_supported']
    assert not summary['scientific_admission'] and card.verify(out,inputs,{})['verified']
