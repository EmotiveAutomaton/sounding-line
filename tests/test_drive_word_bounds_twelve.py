"""Exercise the complete serialized enclosure handler with a known token model."""
from pathlib import Path
from types import SimpleNamespace
import json
import pytest

from runners.drive.cards import timing_word_bounds_twelve as card


def setup(monkeypatch,tmp_path):
    import torch
    pieces={1:b'a',2:b' ',3:b'!'}
    class Tokenizer:
        eos_token_id=0
        def __call__(self,text,**kwargs):
            return dict(input_ids=[{'a':1,' ':2,'!':3}[c] for c in text],offset_mapping=[(i,i+1) for i in range(len(text))])
        def decode(self,ids,**kwargs):return b''.join(pieces[i] for i in ids).decode()
    class Model:
        def __call__(self,input_ids,**kwargs):
            logits=torch.log(torch.tensor([.1,.4,.4,.1],dtype=torch.float32))
            return SimpleNamespace(logits=logits.repeat(1,len(input_ids[0]),1))
    rows=[dict(domain=domain,index=i,is_word=True,prefix=' ',target='a') for domain in ('a','b') for i in (0,1)]
    monkeypatch.setattr(card,'source',lambda inputs,config: (dict(fixture=True),rows,{},pieces))
    monkeypatch.setattr(card,'load_model',lambda manifest:(Model(),Tokenizer(),torch))
    marker=tmp_path/'input.json';marker.write_text('{}',encoding='utf8')
    return dict(source=str(marker)),tmp_path/'output'


def test_complete_execute_verify_reentry_and_mutation(monkeypatch,tmp_path):
    inputs,output=setup(monkeypatch,tmp_path)
    first=card.execute(output,inputs,card.CONFIG)
    assert first['targets']==4 and first['native_forwards']>0
    assert not first['scientific_admission']
    assert card.verify(output,inputs,card.CONFIG)['full_oracle_and_event_replay']
    assert card.execute(output,inputs,card.CONFIG)==first
    before=json.loads((output/'targets/0.json').read_text())
    before['row_index']=999
    (output/'targets/0.json').write_text(json.dumps(before),encoding='utf8')
    with pytest.raises(ValueError,match='intermediate/output changed'):
        card.verify(output,inputs,card.CONFIG)


def test_resource_yield_does_not_emit_primary(monkeypatch,tmp_path):
    inputs,output=setup(monkeypatch,tmp_path)
    output.mkdir();(output/'YIELD_REQUEST.json').write_text('{}')
    result=card.execute(output,inputs,card.CONFIG)
    assert result['status']=='yielded' and result['completed']==1
    assert not (output/'PRIMARY.json').exists()


def test_only_capacity_changes_from_frozen_native_handler():
    import ast
    from runners.drive.cards import timing_word_bounds_refined as previous
    def functions(module):
        tree=ast.parse(Path(module.__file__).read_text(encoding='utf8'))
        return [ast.dump(node,include_attributes=False) for node in tree.body
                if isinstance(node,(ast.FunctionDef,ast.Import,ast.ImportFrom))]
    assert functions(card)==functions(previous)
    assert card.CONFIG==dict(previous.CONFIG,max_nodes_per_event=12)
    assert previous.CONFIG['max_nodes_per_event']==8
