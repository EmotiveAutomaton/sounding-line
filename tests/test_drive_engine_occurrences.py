"""Known occurrence identities and intentional failures, never corpus scores."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.engine_occurrences import final_document, source_atoms
from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.events_p5 import extract_session


def event(ms, ops=None, source='user', doc=None, name=None):
    value = dict(eventName=name or ('system-initialize' if doc is not None else 'text-insert'),
                 eventTimestamp=ms, eventSource=source)
    if doc is not None:
        value['currentDoc'] = doc
    if ops is not None:
        value['textDelta'] = dict(ops=ops)
    return value


def checked(events):
    frozen = replay_words(events)
    p5 = extract_session(events, dict(final_document=frozen['final_document'], edits=[]))
    value = final_document(events, {'session': 'constructed-only'},
        expected_final=frozen['final_document'], expected_p6=frozen['words'], p5_sentences=p5['sentences'])
    assert value['document']['text'] == frozen['final_document']
    spans = value['document']['provenance']
    assert [r['start'] for r in spans] == [0] + [r['end'] for r in spans[:-1]] if spans else not frozen['final_document']
    assert sum(r['end'] - r['start'] for r in spans) == len(frozen['final_document'])
    return value


def test_repeated_spelling_and_identical_replacement_keep_original_identity():
    events = [event(0, doc=''), event(100, [{'insert': 'cat cat '}]),
              event(200, [{'delete': 3}, {'insert': 'cat'}])]
    value = checked(events)
    rows = value['occurrences']
    assert rows[0]['final_codepoints'] is None
    assert rows[1]['final_codepoints'] == [4, 7]
    assert rows[2]['final_codepoints'] == [0, 3]
    assert rows[0]['character_ids'] != rows[2]['character_ids']
    assert value['support']['original_words'] == 3
    assert value['support']['intact_final_words'] == 2


def test_internal_insertion_does_not_join_old_word_to_new_token():
    events = [event(0, doc=''), event(100, [{'insert': 'cat '}]),
              event(200, [{'retain': 1}, {'insert': 'h'}])]
    value = checked(events)
    assert value['document']['text'] == 'chat '
    assert value['occurrences'][0]['final_codepoints'] is None
    assert value['occurrences'][1]['final_codepoints'] == [0, 4]


def test_unicode_codepoints_utf16_casefold_and_combining_mark_are_distinct():
    events = [event(0, doc=''), event(100, [{'insert': '😀 Straße e\u0301\r\ncat '}]),
              event(200, [{'delete': 2}])]
    value = checked(events)
    assert value['document']['text'] == ' Straße e\u0301\r\ncat '
    assert value['occurrences'][0]['final_codepoints'] is None
    assert value['occurrences'][1]['final_codepoints'] == [1, 7]
    assert value['occurrences'][1]['character_ids'] == list(range(2, 8))
    # P6 and the engine may tokenize a combining mark differently. This adapter
    # preserves P6 spans; a future exact export join must disclose unsupported rows.
    assert value['document']['text'][1:7] == 'Straße'


def test_prompt_and_accepted_text_do_not_become_typed_occurrences():
    events = [event(0, doc='Prompt\n'), event(10, name='suggestion-open'),
              event(20, name='suggestion-select'),
              event(30, [{'retain': 7}, {'insert': 'cat\n'}], source='api'),
              event(40, [{'retain': 10}, {'insert': ' typed'}])]
    value = checked(events)
    assert value['document']['text'] == 'Prompt\ncat typed\n'
    assert value['support']['original_words'] == 1
    assert value['support']['intact_final_words'] == 1
    provenance = value['document']['provenance']
    assert {r['source'] for r in provenance} == {'prompt', 'accepted', 'typed'}
    assert [r for r in provenance if r['occurrenceId'].startswith('p6:')][0]['start'] == 11


def test_api_deletion_and_reinsertion_are_not_human_survival():
    events = [event(0, doc=''), event(100, [{'insert': 'cat '}]),
              event(200, [{'delete': 3}, {'insert': 'cat'}], source='api')]
    value = checked(events)
    assert value['support']['intact_final_words'] == 0
    assert value['document']['provenance'][0]['source'] == 'api_unknown'


def test_mutated_frozen_records_and_partition_refuse():
    events = [event(0, doc=''), event(100, [{'insert': 'cat '}])]
    words = replay_words(events)['words']
    bad = copy.deepcopy(words); bad[0]['pause_seconds'] = 999
    with pytest.raises(ValueError, match='P6'):
        final_document(events, {}, expected_p6=bad)
    with pytest.raises(ValueError, match='final document'):
        final_document(events, {}, expected_final='dog ')
    bad_p5 = [dict(start_codepoint=0, end_codepoint=4, text='cat ', origin_counts={'prompt': 3}, writer_typed=False)]
    with pytest.raises(ValueError, match='P5 source partition'):
        final_document(events, {}, p5_sentences=bad_p5)
    with pytest.raises(ValueError, match='P5 sentence coverage'):
        final_document(events, {}, p5_sentences=[])


def test_empty_and_malformed_sources_are_explicit():
    assert checked([event(0, doc='')])['support']['original_occurrences'] == 0
    with pytest.raises((ValueError, UnicodeDecodeError)):
        source_atoms([event(0, doc='😀'), event(100, [{'delete': 1}])])
    with pytest.raises(ValueError, match='chronology'):
        source_atoms([event(100, doc=''), event(0, [{'insert': 'cat '}])])
    with pytest.raises(ValueError, match='boundary'):
        source_atoms([event(0, doc='a'), event(100, [{'retain': 2}])])
    # UTF16 operations are a single delta; two adjacent deletes may remove both
    # surrogate halves. The resulting document must still decode exactly.
    assert source_atoms([event(0, doc='😀x'), event(100, [{'delete': 1}, {'delete': 1}])])[0] == 'x'


def test_fresh_process_reconstructs_exact_serialized_input(tmp_path):
    events = [event(0, doc=''), event(100, [{'insert': '😀 cat cat '}]),
              event(200, [{'retain': 3}, {'delete': 3}, {'insert': 'dog'}])]
    expected = checked(events)
    src, dst = tmp_path / 'events.json', tmp_path / 'input.json'
    src.write_text(json.dumps(events, ensure_ascii=False), encoding='utf8')
    code = "import json,sys;from runners.drive.engine_occurrences import final_document;v=json.load(open(sys.argv[1],encoding='utf8'));json.dump(final_document(v,{'session':'constructed-only'}),open(sys.argv[2],'x',encoding='utf8'),ensure_ascii=False)"
    child = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', code, str(src), str(dst)],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30,
        env={**os.environ, 'PYTHONHASHSEED': '721'},
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(dst.read_text(encoding='utf8')) == expected
