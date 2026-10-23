from pathlib import Path

import pytest

from runners.drive.cards import week_genre_inputs_recovery as card
from tests.test_drive_week_genre_inputs import fixture as old_fixture, population, write


def fixture(root):
    root = Path(root).resolve(); inputs = old_fixture(root)
    complete = card.read(root/'COMPLETE.json')
    for row in population():
        path = root/'output/sessions'/f"{row['session']}.json.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        card.gzip_equal(path, {k: row[k] for k in ('session', 'writer', 'prompt', 'timestamp')})
        complete['outputs'][path.relative_to(root).as_posix()] = card.filehash(path)
    write(root/'output/PRIMARY.json', dict(source_audit=dict(sessions=120)))
    complete['outputs']['output/PRIMARY.json'] = card.filehash(root/'output/PRIMARY.json')
    roster = card.read(root/'ROSTER.json')
    roster.append(dict(session='upstream-only', writer='outside', prompt='p0', timestamp=0, domain='creative'))
    write(root/'ROSTER.json', roster)
    write(root/'foundation/PLAN.json', dict(pins={'ROSTER.json': card.filehash(root/'ROSTER.json')}))
    write(root/'foundation/COMPLETE.json', dict(status='COMPLETE', plan_sha256=card.filehash(root/'foundation/PLAN.json')))
    write(root/'COMPLETE.json', complete)
    return inputs


def test_full_recovery_preserves_exact_old_matching_with_upstream_extras(tmp_path):
    inputs = fixture(tmp_path/'source'); output = tmp_path/'output'
    expected, matches = card.base.match(population())
    card.execute(output, inputs, card.CONFIG)
    assert card.verify(output, inputs, card.CONFIG)['exact_primary_population']
    assert card.read(output/'SUPPORT.json') == expected
    assert card.gzread(output/'MATCHES.json.gz') == matches
    assert card.read(output/'SOURCE_POPULATION.json')['upstream_only_sessions'] == ['upstream-only']


@pytest.mark.parametrize('mutation', ['missing_word', 'missing_raw', 'changed_primary', 'count', 'identity', 'duplicate'])
def test_population_and_identity_defects_refuse_even_if_receipts_rebound(tmp_path, mutation):
    root = tmp_path/'source'; inputs = fixture(root)
    complete = card.read(root/'COMPLETE.json')
    if mutation == 'missing_word':
        path = root/'p6/INDEX.json'; write(path, card.read(path)[1:])
        c = card.read(root/'p6/COMPLETE.json'); c['outputs']['INDEX.json'] = card.filehash(path)
        write(root/'p6/COMPLETE.json', c)
    elif mutation == 'missing_raw':
        path = root/'ROSTER.json'; write(path, card.read(path)[1:])
        write(root/'foundation/PLAN.json', dict(pins={'ROSTER.json': card.filehash(path)}))
        write(root/'foundation/COMPLETE.json', dict(status='COMPLETE', plan_sha256=card.filehash(root/'foundation/PLAN.json')))
    elif mutation == 'changed_primary':
        with (root/'output/sessions/0-creative-0.json.gz').open('ab') as stream: stream.write(b'x')
    elif mutation == 'count':
        path = root/'output/PRIMARY.json'; write(path, dict(source_audit=dict(sessions=119)))
        complete['outputs']['output/PRIMARY.json'] = card.filehash(path)
    elif mutation in ('identity', 'duplicate'):
        name = 'output/sessions/changed.json.gz'
        row = card.gzread(root/'output/sessions/0-creative-0.json.gz')
        if mutation == 'identity':
            row['writer'] = 'changed'
            complete['outputs'].pop('output/sessions/0-creative-0.json.gz')
        card.gzip_equal(root/name, row); complete['outputs'][name] = card.filehash(root/name)
    write(root/'COMPLETE.json', complete)
    with pytest.raises(ValueError): card.execute(tmp_path/'output', inputs, card.CONFIG)


def test_saved_population_and_manifest_tamper_refuse(tmp_path):
    inputs = fixture(tmp_path/'source'); output = tmp_path/'output'
    card.execute(output, inputs, card.CONFIG)
    saved = card.read(output/'SOURCE_POPULATION.json')
    write(output/'SOURCE_POPULATION.json', dict(saved, upstream_only_sessions=[]))
    with pytest.raises(ValueError, match='replay differs'): card.verify(output, inputs, card.CONFIG)
