from pathlib import Path
import pytest
from runners.drive.cards import week_genre_features_paths as card
from tests.test_drive_week_genre_compare import fixture,write


def mixed_fixture(root):
    inputs=fixture(root);root=Path(root).resolve();path=root/'PINS.json'
    pins=card.read(path)
    write(path,{(k.replace('/', '\\') if k.startswith('results/') else k):v for k,v in pins.items()})
    return inputs


def test_mixed_native_and_posix_paths_full_feature_replay(tmp_path):
    inputs=mixed_fixture(tmp_path/'source');out=tmp_path/'output'
    card.execute(out,inputs,card.CONFIG)
    assert card.verify(out,inputs,card.CONFIG)['verified']
    assert card.read(out/'SUMMARY.json')['sessions']==120


def test_conflicting_normalized_pin_is_not_overwritten():
    with pytest.raises(ValueError,match='Conflicting'):
        card.normalize_pins({'folder/file':'a','folder\\file':'b'})


def test_changed_canonical_bytes_still_refused(tmp_path):
    inputs=mixed_fixture(tmp_path/'source');root=tmp_path/'source'
    target=next((root/'results').rglob('*.json'));write(target,dict(events=[dict(changed=True)]))
    with pytest.raises(ValueError,match='pin differs'):
        card.execute(tmp_path/'output',inputs,card.CONFIG)
