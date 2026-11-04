from collections import Counter
import pytest
from runners.drive.cards import week4_s1_nuisance as n

def test_known_geometry_and_exact_feature_vector():
    assert all(n.known_check().values())

def test_unicode_predecessor_uses_codepoints_and_retains_paragraph():
    typed=dict(initial_document='😀',edits=[dict(ordinal=1,source='user',operations=[dict(retain=2),dict(insert='\n')]),
        dict(ordinal=2,source='user',operations=[dict(retain=3),dict(insert='a')])],final_document='😀\na')
    assert n.onset_geometry(typed,{2:dict(previous_ordinal=1)})[2]==dict(state='supported',pair='\na',paragraph_boundary=True)
    typed['final_document']='wrong'
    with pytest.raises(ValueError,match='replay'):n.onset_geometry(typed,{2:dict(previous_ordinal=1)})

def test_missing_history_and_changed_occurrence_refuse():
    record=dict(words=[dict(index=0,ordinal=1)],timestamp=0)
    window=dict(indices=[0],ordinals=[1])
    assert n.features(window,record,{}, {},Counter(),0,0)==(None,'empty own frequency history')
    window['ordinals']=[2]
    with pytest.raises(ValueError,match='occurrence'):n.features(window,record,{}, {},Counter(),0,0)

def test_full_native_interface_and_changed_output(tmp_path):
    c=n.configuration('constructed');n.execute(tmp_path,{},c)
    assert n.verify(tmp_path,{},c)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='summary'):n.verify(tmp_path,{},c)
