import pytest
from runners.drive.cards import week4_s1_window_textures as texture
from runners.drive.cards import week4_typed_windows as original


@pytest.mark.parametrize('size', [5, 12])
def test_exact_variant_replay_and_mutation(tmp_path, size):
    config = texture.configuration(size, 'constructed')
    texture.execute(tmp_path, {}, config)
    assert texture.verify(tmp_path, {}, config)['complete_source_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError, match='replay'):
        texture.verify(tmp_path, {}, config)


@pytest.mark.parametrize('size', [5, 12])
def test_source_exclusions_at_each_length(size):
    words, times = texture.fixture(size)
    times[0]['interval_seconds'] = 100.
    windows, _ = original.session_windows(dict(words=words), times, {'the'}, size)
    assert windows[0]['indices'] == list(range(size))
    times[1]['interval_seconds'] = 61.
    windows, counts = original.session_windows(dict(words=words), times, {'the'}, size)
    assert counts['window_break'] == 1 and windows[0]['indices'][0] == size
    words[2]['previous_typed_token_index'] = None
    windows, counts = original.session_windows(dict(words=words), times, {'the'}, size)
    assert counts['stop_with_disconnected_window'] == 1
    before = (windows, counts)
    for word in words:
        word['revised'] = True
    assert before == original.session_windows(dict(words=words), times, {'the'}, size)


def test_undeclared_length_refused():
    with pytest.raises(ValueError, match='declared'):
        texture.configuration(8, 'full')
