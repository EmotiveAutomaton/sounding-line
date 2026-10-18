from runners.drive.cards import events_d32_canonical_v2 as card
from runners.drive.cards import events_d32_canonical as old
from runners.drive.cards.menus_io import read
from tests.test_drive_cards_d32_canonical import native_fixture


def test_separate_pilot_projection_and_identical_scientific_files(tmp_path):
    inputs=native_fixture(tmp_path/'source')
    a=tmp_path/'old';b=tmp_path/'new'
    old.execute(a,inputs,old.PILOT_CONFIG)
    card.execute(b,inputs,card.PILOT_CONFIG)
    assert card.verify(b,inputs,card.PILOT_CONFIG)['verified']
    for name in ['SUMMARY.json','SOURCE_AUDIT.json','ROWS.json','FIT.json','BINDING.json']:
        assert (a/name).read_bytes()==(b/name).read_bytes()
    for phase in ['bootstrap','controls']:
        for path in (a/phase).glob('*.json'):assert path.read_bytes()==(b/phase/path.name).read_bytes()
    timing=read(b/'FIRST_TENTH.json')
    assert timing['projected_full_main_seconds']>timing['projected_seconds']
    # This field is consumed by admission; full-main cost remains distinct.
    assert 'pilot' in card.__doc__
