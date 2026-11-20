import hashlib

import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_lattice_source_v1 as s


def row(member='0057', route='LD1', **kw):
    value = {n: '3' for n in s.columns(member, route)}
    value.update(id='constructed-a', day='1', interaction='1')
    value.update(kw)
    return value


def prepare(rows, member='0057', route='LD1'):
    return s.prepare_people([pd.DataFrame(rows)], member, route, ['', 'NA'], lambda: None)


def test_context_mapping_and_failure_reversal():
    p, c = prepare([row(int_success='6', int_ashamed='2', occup_ashamed='5'),
                    row(interaction='2', occup_success='1', occup_ashamed='4')])
    assert p[0]['ratings']['failure'] == [1, 6]
    assert p[0]['ratings']['company'] == [1, 0]
    assert p[0]['ratings']['ashamed'] == [2, 4]
    assert c['selected_rows'] == 2


def test_missing_secondary_does_not_remove_primary():
    p, _ = prepare([row(int_lonely='NA'), row(int_ashamed='NA'), row(day='NA')])
    ids, _, c = s.complete_panel(p, ['failure', 'company', 'ashamed', 'sad'])
    assert ids.tolist() == [0, 0]
    assert c['missing_rows'] == 1
    assert p[0]['days'][2] != p[0]['days'][2]
    assert np.isnan(p[0]['ratings']['lonely'][0])


def test_member_0056_does_not_fabricate_absent_items():
    p, _ = prepare([row('0056')], '0056')
    assert 'lonely' not in p[0]['ratings'] and 'excluded' not in p[0]['ratings']
    with pytest.raises(ValueError, match='absent'):
        s.complete_panel(p, ['lonely'])


def test_identity_grouping_is_stable_and_not_exported():
    p, c = prepare([row(id='constructed-z'), row(id='constructed-a'), row(id='constructed-z')])
    assert [x['source_ordinals'] for x in p] == [[1], [0, 2]]
    assert 'constructed' not in repr(p)
    assert c['identity_fields_exported'] is False
    assert c['temporal_order_inferred'] is False


def test_missing_and_other_context_counts():
    p, c = prepare([row(route='LD3', id=''), row(route='LD3', interaction='NA'),
                    row(route='LD3'), row(route='LD3', interaction='2')], route='LD3')
    assert (c['missing_id_rows'], c['missing_context_rows'], c['other_context_rows'], c['selected_rows']) == (1, 1, 1, 1)
    assert len(p) == 1
    assert set(s.ACTIVITY) <= p[0]['ratings'].keys()


@pytest.mark.parametrize('bad', ['0', '7', 'nan', 'inf', 'not-a-rating'])
def test_bad_ratings_refuse(bad):
    with pytest.raises(ValueError):
        prepare([row(int_ashamed=bad)])


@pytest.mark.parametrize('bad', ['0', '3', 'nan', 'x'])
def test_unknown_context_refuses(bad):
    with pytest.raises(ValueError):
        prepare([row(interaction=bad)])


def test_role_support_cannot_materialize_feelings():
    wanted = s.columns('0057', 'LD2-support')
    assert not any(n.startswith(('int_', 'occup_')) for n in wanted)
    p, _ = prepare([row(route='LD2-support', interaction_partner1='7', no_interactionpartner='1')], route='LD2-support')
    assert set(p[0]['ratings']) == {'partner_count', 'role', 'criticised', 'leadership'}


def test_ld2_products_keep_complete_event_and_feeling_sets():
    p, _ = prepare([row(route='LD2-product')], route='LD2-product')
    assert set(s.STATUS) <= p[0]['ratings'].keys()
    assert {'angry', *s.FEAR_LIKE, 'leadership', 'selfesteem', 'superior'} <= p[0]['ratings'].keys()


def test_wrong_columns_and_missing_token_contract_refuse():
    r = row(); r['private_text'] = 'must not materialize'
    with pytest.raises(ValueError, match='columns'):
        prepare([r])
    with pytest.raises(ValueError, match='tokens'):
        s.prepare_people([], '0057', 'LD1', None, lambda: None)


def test_source_hash_whitelist_and_midread_mutation(tmp_path):
    path = tmp_path / 'constructed.tsv'
    frame = pd.DataFrame([dict(row(), private_text='not selected')])
    frame.to_csv(path, sep='\t', index=False)
    pin = dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    frames = list(s.selected_frames(path, pin, '0057', 'LD1', lambda: None))
    assert tuple(frames[0].columns) == s.columns('0057', 'LD1')
    with pytest.raises(ValueError, match='digest'):
        list(s.selected_frames(path, dict(pin, sha256='0'*64), '0057', 'LD1', lambda: None))
    stream = s.selected_frames(path, pin, '0057', 'LD1', lambda: None)
    next(stream)
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='changed'):
        next(stream)


def test_empty_panels_keep_explicit_shape_and_counts():
    ids, values, counts = s.complete_panel([], ['ashamed'])
    assert ids.shape == (0,) and values['ashamed'].shape == (0,)
    assert counts['retained_rows'] == 0
    assert counts['support_not_yet_adjudicated']


def test_no_hidden_minimum_or_row_alignment_repair():
    p, _ = prepare([row()])
    assert s.complete_panel(p, ['ashamed'])[2]['retained_rows'] == 1
    p[0]['ratings']['ashamed'].append(2)
    with pytest.raises(ValueError, match='alignment'):
        s.complete_panel(p, ['ashamed'])
