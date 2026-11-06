import copy
import json
import pytest
from runners.drive.cards import week4_auth_collection as c


def test_exact_row_join_and_both_writer_roles():
    data = c.fixture()
    rows, summary = c.assemble(*data, c.configuration('constructed'))
    assert summary['pairs'] == 80 and summary['blocks'] == 40
    by_request = data[3]
    sources = {r['session']: r for r in data[0]}
    for row in rows:
        assert row['score'] == by_request[row['custom_id']]
        assert row['same_writer'] == (row['left_writer'] == row['right_writer'])
        assert row['right_writer'] == sources[row['right_session']]['writer']
        assert 'texts' not in row
    assert {g['both_role_writers'] for g in summary['by_genre'].values()} == {4}
    assert not summary['scientific_effect_computed']


@pytest.mark.parametrize('change', ['truth', 'prompt', 'text', 'missing', 'duplicate',
                                  'extra_label', 'bad_label', 'calibration', 'request', 'block'])
def test_corrupted_or_incomplete_join_refused(change):
    data = list(copy.deepcopy(c.fixture()))
    if change == 'truth':
        data[1][0]['same_writer'] = not data[1][0]['same_writer']
    if change == 'prompt':
        data[1][0]['prompts'][0] = 'wrong'
    if change == 'text':
        data[1][0]['texts'][0] = 'wrong'
    if change == 'missing':
        data[1].pop()
    if change == 'duplicate':
        data[1][1] = copy.deepcopy(data[1][0])
    if change == 'extra_label':
        data[3]['unexpected'] = 1
    if change == 'bad_label':
        data[3][data[2][0]['custom_id']] = True
    if change == 'calibration':
        data[4][0] = data[1][0]['pair_id']
    if change == 'request':
        data[2][0]['params']['messages'][0]['content'] = '{}'
    if change == 'block':
        data[1][0]['block'] = 'wrong'
    with pytest.raises(ValueError):
        c.assemble(*data, c.configuration('constructed'))


def raw(score='{"score": 4}', identity='a'):
    return json.dumps(dict(custom_id=identity, result=dict(type='succeeded', message=dict(
        model='test-model', stop_reason='end_turn', content=[dict(type='text', text=score)]))))


@pytest.mark.parametrize('score', ['{"score": true}', '{"score": 10}',
                                  '{"score": 4, "score": 5}', '{"score": 4, "extra": 1}'])
def test_strict_independent_parser(score):
    with pytest.raises(ValueError):
        c.parse_raw([raw(score)], [{'custom_id': 'a'}], 'test-model')


def test_parser_coverage_and_order():
    requests = [{'custom_id': 'a'}, {'custom_id': 'b'}]
    assert c.parse_raw([raw(identity='b'), raw()], requests, 'test-model') == {'a': 4, 'b': 4}
    for lines in ([], [raw()], [raw(), raw()], [raw(), raw(identity='wrong')]):
        with pytest.raises(ValueError):
            c.parse_raw(lines, requests, 'test-model')


def test_actual_handler_reentry_and_mutation(tmp_path):
    config = c.configuration('constructed')
    c.execute(tmp_path, {}, config)
    before = (tmp_path/'PRIVATE_ROWS.json').read_bytes()
    c.execute(tmp_path, {}, config)
    assert c.verify(tmp_path, {}, config)['complete_identity_join']
    assert (tmp_path/'PRIVATE_ROWS.json').read_bytes() == before
    (tmp_path/'PRIVATE_ROWS.json').write_text('[]', encoding='utf8')
    with pytest.raises(ValueError):
        c.verify(tmp_path, {}, config)
    with pytest.raises(ValueError):
        c.execute(tmp_path, {'foreign': 'source'}, config)


def test_unlanded_or_foreign_inputs_refused():
    with pytest.raises(ValueError):
        c.load({})
    with pytest.raises(ValueError):
        c.load({'main_landing': 'different.json'})
