import pytest
from runners.drive.cards import week4_t4_menus_v2 as m

def test_real_windows_pin_representation_and_conflicting_aliases():
    assert m.normalize_pins({'results\\prepared\\a.json':'abc'})=={'results/prepared/a.json':'abc'}
    assert m.normalize_pins({'a\\b':'abc','a/b':'abc'})=={'a/b':'abc'}
    with pytest.raises(ValueError,match='Conflicting'):
        m.normalize_pins({'a\\b':'abc','a/b':'changed'})

def test_corrected_actual_interface_preserves_replay_and_tamper_refusal(tmp_path):
    config=m.configuration('constructed');m.execute(tmp_path,{},config)
    assert m.verify(tmp_path,{},config)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='aggregate'):m.verify(tmp_path,{},config)
