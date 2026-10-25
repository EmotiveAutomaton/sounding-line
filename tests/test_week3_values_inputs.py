import copy
import gzip
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_values_inputs as card
from runners.stage14.common import filehash, freeze, read
from tests.test_drive_engine_export_join import case


def fixture(root):
    root = Path(root); prepared = root/'prepared'; out = prepared/'output'; out.mkdir(parents=True)
    rows = [dict(writer='w'+str(w), conversation='c'+str(j), turn=j, prompt='p'+str(j), half=j%2,
                 explanation=f'Constructed explanation writer {w} item {j}') for w in range(30) for j in range(20)]
    with gzip.open(out/'COMPARISONS.jsonl.gz', 'wt', encoding='utf8') as stream:
        stream.writelines(json.dumps(r)+'\n' for r in rows)
    freeze(out/'SPLITS.json', {'writer_splits':{'w'+str(w):{} for w in range(30)}})
    freeze(out/'SUMMARY.json', dict(card='CA1-inputs', state='inputs_ready',
        output_hashes={n:filehash(out/n) for n in ('COMPARISONS.jsonl.gz','SPLITS.json')}))
    freeze(prepared/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={'output/SUMMARY.json':filehash(out/'SUMMARY.json')}))
    ev = root/'ev'; ev.mkdir(); record = copy.deepcopy(case('unicode')['record'])
    sid = record['document']['keys']['session']
    with gzip.open(ev/'session.json.gz', 'wt', encoding='utf8') as stream: json.dump(record, stream)
    freeze(ev/'INDEX.json', [dict(session=sid, file='session.json.gz', sha256=filehash(ev/'session.json.gz'))])
    freeze(ev/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True, outputs={'INDEX.json':filehash(ev/'INDEX.json')}))
    roster = root/'roster'; roster.mkdir()
    freeze(roster/'ROSTER.json', [dict(session=sid, domain='argumentative'),dict(session='raw-only', domain='argumentative')])
    freeze(roster/'COMPLETE.json', dict(status='complete', outputs={'ROSTER.json':filehash(roster/'ROSTER.json')}))
    return dict(prepared_summary=str(out/'SUMMARY.json'), prepared_complete=str(prepared/'COMPLETE.json'),
        ev_index=str(ev/'INDEX.json'), ev_complete=str(ev/'COMPLETE.json'), roster=str(roster/'ROSTER.json'),
        roster_complete=str(roster/'COMPLETE.json'))


def test_frozen_per_person_sample_independent_of_order_and_choices():
    rows = [dict(writer='a', conversation='c'+str(j), turn=j, prompt='p'+str(j), half=j%2,
                 explanation='reason '+str(j), choice=0) for j in range(30)]
    first, census = card.choice_sample(rows, ['a'])
    for row in rows: row['choice'] = 3
    assert card.choice_sample(rows[::-1], ['a']) == (first, census)
    assert len(first) == 10 and census[0]['available_explanations'] == 30
    with pytest.raises(ValueError, match='population'): card.choice_sample(rows, ['a','missing'])


def test_deduplication_preserves_every_private_join():
    rows, joins = card.deduplicate([dict(text='same', link={'writer':w}) for w in ('a','b')])
    assert len(rows) == 1 and len(joins[rows[0]['item_id']]) == 2
    assert set(rows[0]) == {'item_id','text'}


def test_surviving_typed_scope_raw_only_and_explicit_empty_status():
    record = copy.deepcopy(case('unicode')['record']); keys = record['document']['keys']
    items, census = card.coauthor_items([record], [dict(session=keys['session'], domain='argumentative'),
                                                dict(session='outside', domain='creative')])
    assert len(items) == 1 and len(census) == 2
    assert items[0]['text'] == card.typed_fragments(record)['document']['text']
    assert census[1]['status'] == 'outside-admitted-canonical-EV-population'
    empty = copy.deepcopy(record); empty['occurrences'] = []
    for span in empty['document']['provenance']:
        span['source'] = 'accepted'; span['occurrenceId'] = 'non-typed:'+str(span['start'])
    empty['support'] = dict(original_occurrences=0,intact_final_occurrences=0,original_words=0,intact_final_words=0)
    items, census = card.coauthor_items([empty], [dict(session=keys['session'], domain='argumentative')])
    assert not items and census[0]['status'] == 'unsupported-no-typed-words'


def test_full_constructed_handler_and_fresh_source_replay(tmp_path):
    inputs = fixture(tmp_path/'inputs'); output = tmp_path/'output'
    summary = card.execute(output, inputs, {'fixture':True})
    assert summary['sampled_explanations'] == 300 and summary['argumentative_sessions'] == 1
    assert summary['raw_roster_only_sessions'] == 1 and not summary['scientific_admission']
    assert card.verify(output, inputs, {'fixture':True})['verified']
    assert len(read(output/'PRIVATE_POPULATION.json')['choice']) == 30
    with pytest.raises(ValueError, match='population'): card.calculate(inputs, {})


def test_source_mutation_cannot_be_hidden_in_fresh_verification(tmp_path):
    inputs = fixture(tmp_path/'inputs'); output = tmp_path/'output'
    card.execute(output, inputs, {'fixture':True})
    Path(inputs['roster']).write_text('[]', encoding='utf8')
    with pytest.raises(ValueError, match='authenticated'): card.verify(output, inputs, {'fixture':True})
