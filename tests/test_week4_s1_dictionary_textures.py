import pytest
from runners.drive.cards import week4_s1_dictionary_textures as t
from runners.drive.cards import week4_typed_windows as original


@pytest.mark.parametrize('size',[100,300])
def test_actual_dictionary_builder_replay_and_tamper(tmp_path,size):
    config=t.configuration(size,'constructed')
    t.execute(tmp_path,{},config)
    assert t.verify(tmp_path,{},config)['complete_source_replay']
    assert t.read(tmp_path/'FROZEN_DICTIONARY.json')['words']==[f'w{i:03d}' for i in range(size)]
    (tmp_path/'FROZEN_DICTIONARY.json').write_text('{}',encoding='utf8')
    with pytest.raises(ValueError,match='replay'):t.verify(tmp_path,{},config)


@pytest.mark.parametrize('size',[100,300])
def test_original_window_rules_remain(size):
    config=t.configuration(size,'full')
    for key in ('seed','window_words','expected_sessions'):assert config[key]==original.CONFIG[key]
    assert config['dictionary_words']==size and config['descendants'] is False


def test_other_size_refused():
    with pytest.raises(ValueError,match='declared'):t.configuration(150,'full')
