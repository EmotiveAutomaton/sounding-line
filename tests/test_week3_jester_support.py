import json
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week3_jester_support as m


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True)+'\n', encoding='utf8')


def fixture(root):
    root = Path(root); out = root/'output'; out.mkdir(parents=True)
    texts = root/'texts.json'
    put(texts, [dict(joke_id=i, text=f'Constructed item {i}') for i in range(1, 151)])
    put(out/'INPUT_BINDING.json', dict(constructed=True))
    put(out/'QUARANTINE.json', dict(numeric_cells=123, blank_cells=28))
    arrays = [np.full((2, 150), np.nan), np.full((1, 150), np.nan)]
    arrays[0][0, :3] = [-10, 0, 10]
    arrays[0][1, 0] = 0
    arrays[1][0, 1] = -1
    chunks=[];offset=0
    for i,a in enumerate(arrays):
        p=out/f'chunks/{i:04}.npy';p.parent.mkdir(exist_ok=True);np.save(p,a)
        unit=dict(rows=len(a),rater_offset=offset,excel_row_first=offset+1,excel_row_last=offset+len(a),sheet='fixture',sheet_index=0)
        put(p.with_suffix('.json'),dict(unit=unit,sha256=m.filehash(p),input_binding_sha256=m.filehash(out/'INPUT_BINDING.json')))
        chunks.append(dict(file=p.relative_to(out).as_posix(),receipt=p.with_suffix('.json').relative_to(out).as_posix(),**unit));offset+=len(a)
    put(out/'RATINGS_INDEX.json',dict(schema=1,dtype='float64',missing='NaN',joke_ids=list(range(1,151)),rows=3,chunks=chunks))
    put(root/'PLAN.json',dict(module='runners.drive.cards.timing_jester_complete_records',config=dict(card='Jester2plus-complete-records',rows_per_chunk=1024),inputs=dict(jester_texts=str(texts)),pins={str(texts):m.filehash(texts)}))
    seal(root)
    return dict(source_complete=str(root/'COMPLETE.json'),source_plan=str(root/'PLAN.json'),jester_texts=str(texts)),dict(mode='constructed',expected_rows=3)


def seal(root):
    put(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,card='Jester2plus-complete-records',outputs={p.relative_to(root).as_posix():m.filehash(p) for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json'}))


def test_all_rows_signs_zero_missing_and_full_replay(tmp_path):
    inputs,config=fixture(tmp_path/'source');dest=tmp_path/'result'
    m.execute(dest,inputs,config);r=m.read(dest/'SOURCE_SUPPORT.json')
    assert r['population_records']==3 and r['records_with_both_item_halves']==1
    assert r['signed_value_counts']==dict(negative=2,zero=2,positive=1,missing=445)
    assert r['per_item_observed'][:4]==[2,2,1,0]
    assert r['ratings_per_record_histogram'][1]==2
    assert r['odd_even_observed_count_histogram'][2][1]==1
    assert not r['scientific_admission'] and not r['demographics_available']
    before={p.name:p.read_bytes() for p in dest.iterdir()}
    assert m.verify(dest,inputs,config)['complete_source_replay']
    m.execute(dest,inputs,config)
    assert before=={p.name:p.read_bytes() for p in dest.iterdir()}
    r['signed_value_counts']['zero']=0;put(dest/'SOURCE_SUPPORT.json',r)
    with pytest.raises(ValueError,match='fresh complete'):m.verify(dest,inputs,config)


def test_changed_input_and_output_refuse(tmp_path):
    inputs,config=fixture(tmp_path/'source')
    Path(inputs['jester_texts']).write_text('[]',encoding='utf8')
    with pytest.raises(ValueError,match='changed predecessor input'):m.census(inputs,config)
    inputs,config=fixture(tmp_path/'second')
    p=tmp_path/'second/output/chunks/0000.npy';a=np.load(p);a[0,0]=1;np.save(p,a)
    with pytest.raises(ValueError,match='changed predecessor output'):m.census(inputs,config)


@pytest.mark.parametrize('attack',['duplicate','gap','bad_sentinel','extra','traversal'])
def test_resealed_invalid_source_refuses(tmp_path,attack):
    root=tmp_path/'source';inputs,config=fixture(root);p=root/'output/RATINGS_INDEX.json';ix=m.read(p)
    if attack=='duplicate':ix['chunks'][1]=ix['chunks'][0]
    elif attack=='gap':ix['chunks'][1]['rater_offset']=3
    elif attack=='traversal':ix['chunks'][0]['file']='../../outside.npy'
    elif attack=='extra':np.save(root/'output/chunks/0002.npy',np.zeros((1,150)))
    else:
        q=root/'output/chunks/0000.npy';a=np.load(q);a[0,0]=99;np.save(q,a)
        receipt=m.read(q.with_suffix('.json'));receipt['sha256']=m.filehash(q);put(q.with_suffix('.json'),receipt)
    put(p,ix);seal(root)
    with pytest.raises(ValueError):m.census(inputs,config)


def test_full_population_and_admitted_predecessor_required(tmp_path):
    inputs,config=fixture(tmp_path/'source')
    with pytest.raises(ValueError,match='whole approved'):m.census(inputs,dict(mode='corpus',expected_rows=3))
    c=m.read(inputs['source_complete']);c['fresh_process_verified']=False;put(Path(inputs['source_complete']),c)
    with pytest.raises(ValueError,match='unadmitted'):m.census(inputs,config)
