from runners.drive.cards.week5_at_scope import select


def test_whole_writer_stratified_scope_is_metadata_only():
    metadata = {f'w{i}': {f's{i}-1': 'creative' if i < 12 else 'argumentative',
                          f's{i}-2': 'creative' if i < 12 else 'argumentative'} for i in range(20)}
    chosen, allocation = select(metadata, 10)
    assert len(chosen) == len(set(chosen)) == 10
    assert allocation == {'creative': 6, 'argumentative': 4}
    assert select(dict(reversed(list(metadata.items()))), 10) == (chosen, allocation)
    assert select(metadata, 20)[0] == sorted(metadata)
