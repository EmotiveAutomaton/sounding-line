import pytest
from runners.drive.cards import week4_s1_gram_textures as t
from runners.drive.cards import week4_typed_windows as original


@pytest.mark.parametrize('size', [3, 5])
def test_known_complete_source_replay_and_tamper(tmp_path, size):
    config = t.configuration(size, 'constructed')
    t.execute(tmp_path, {}, config)
    assert t.verify(tmp_path, {}, config)['complete_source_replay']
    (tmp_path / 'SUMMARY.json').write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='replay'):
        t.verify(tmp_path, {}, config)


@pytest.mark.parametrize('size', [3, 5])
def test_sentence_boundaries_occurrences_and_placeholder_refusal(size):
    words = [dict(token='a', sentence_start=i in (0, 6)) for i in range(12)]
    grams = t.window_implementation(size).__globals__['skeleton_grams']
    assert grams(words, {'a'}) == [['a'] * size] * (2 * (7 - size))
    assert grams(words, set()) == []
    assert original.skeleton_grams.__defaults__ == (4,)


@pytest.mark.parametrize('size', [3, 5])
def test_only_declared_axis_changes(size):
    config = t.configuration(size, 'full')
    for key in ('seed', 'window_words', 'dictionary_words', 'expected_sessions'):
        assert config[key] == original.CONFIG[key]
    assert config['gram_words'] == size and config['descendants'] is False


def test_undeclared_gram_size_refused():
    with pytest.raises(ValueError, match='declared'):
        t.configuration(4, 'full')
