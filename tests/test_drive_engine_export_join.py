"""Known identities against retained actual-exporter outputs; no model claims."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.engine_export_join import join_exports, typed_fragments
from runners.drive.engine_occurrences import final_document
from tests.test_drive_engine_occurrences import event

FIXTURE = Path(__file__).parent/'fixtures/ev_export_join.json'


def case(name):
    return next(c for c in json.loads(FIXTURE.read_text(encoding='utf8'))['cases'] if c['name'] == name)


def run(c):
    return join_exports(c['rows'], [c['record']], [c['export']])


def test_replacement_never_takes_identical_later_word_score():
    c = case('replacement'); result = run(c)
    assert [r['original'] for r in result['rows']] == c['rows']
    assert result['rows'][0]['engine'] is None
    assert result['rows'][0]['disposition'] == 'not-intact-final-word'
    assert [r['engine']['word_index'] for r in result['rows'][1:]] == [1, 0]
    assert result['rows'][1]['engine']['departure'] == c['export']['words'][1]['departure']
    assert not result['scientific_admission']


def test_unicode_and_engine_word_boundaries_have_explicit_support():
    c = case('unicode'); result = run(c)
    assert result['support']['dispositions'] == {'engine-held-out': 2,
        'engine-no-exact-word-match': 1, 'engine-not-content': 1, 'engine-scored': 6}
    supported = [c['record']['document']['text'][slice(*r['final_codepoints'])]
                 for r in result['rows'] if r['disposition'] == 'engine-scored']
    assert supported == ['café', 'e', "can't", 'unusual', 'words', 'return']
    unmatched = [r for r in result['rows'] if r['disposition'] == 'engine-no-exact-word-match']
    assert [c['record']['document']['text'][slice(*r['final_codepoints'])] for r in unmatched] == ['bar']
    for r in result['rows']:
        if r['engine'] is None:
            assert r['disposition'] != 'engine-scored'
        else:
            assert r['final_codepoints'] == c['export']['words'][r['engine']['word_index']]['span']['codepoints']
    c['rows'].append(dict(c['rows'][0], session='outside-pilot'))
    r = run(c)['rows'][-1]
    assert r['disposition'] == 'outside-input-cohort' and r['engine'] is None


def test_no_content_is_unsupported_not_zero():
    result = run(case('unsupported'))
    assert result['support']['dispositions'] == {'engine-unsupported-document': 2}
    assert all(r['engine'] is None for r in result['rows'])
    assert result['engine_export_consumed'] and not result['engine_scored']


@pytest.mark.parametrize('mutation', ['keys', 'hash', 'record-hash', 'provenance',
    'utf8', 'utf16', 'slice', 'allocated', 'intersection', 'nan', 'departure',
    'duplicate', 'denominator', 'region', 'held-score'])
def test_corrupt_exports_refuse(mutation):
    c = case('unicode'); e = c['export']; w = e['words'][0]
    if mutation == 'keys': e['keys']['writer'] = 'other'
    elif mutation == 'hash': e['textSha256'] = '0'*64
    elif mutation == 'record-hash': e['inputRecordSha256'] = '0'*64
    elif mutation == 'provenance': e['provenanceSha256'] = '0'*64
    elif mutation == 'utf8': w['span']['utf8'][0] += 1
    elif mutation == 'utf16': w['span']['utf16'][0] += 1
    elif mutation == 'slice': w['span']['exact'] = 'same-looking substitute'
    elif mutation == 'allocated': w['allocatedSpan']['codepoints'][1] -= 1
    elif mutation == 'intersection': w['provenanceIntersections'] = []
    elif mutation == 'nan': w['allocatedTokenLossNats'] = float('nan')
    elif mutation == 'departure': w['departure'] += 1
    elif mutation == 'duplicate': e['words'].append(copy.deepcopy(w))
    elif mutation == 'denominator': e['normalization']['words'] += 1
    elif mutation == 'region': e['regions'][0]['start'] += 1
    elif mutation == 'held-score': next(w for w in e['words'] if w['heldOut'])['departure'] = 0.
    with pytest.raises(ValueError): run(c)


def test_typed_runs_keep_gaps_and_original_boundaries():
    c = case('mixed'); before = copy.deepcopy(c['record']); result = typed_fragments(c['record'])
    doc = result['document']
    assert c['record'] == before
    assert doc['text'] == 'left\n\nright'
    assert doc['variant'] == 'writer-typed-fragments'
    assert result['support'] == dict(typed_codepoints=9, contiguous_runs=2, nonwhitespace_typed_codepoints=9)
    assert doc['fragmentConstruction']['synthetic_separator_codepoints'] == 2
    assert [m['source_codepoints'] for m in doc['fragmentConstruction']['mappings']] == [[0,4],[9,14]]
    assert [p['source'] for p in doc['provenance']] == ['typed','synthetic-boundary','typed']
    for m in doc['fragmentConstruction']['mappings']:
        a,b = m['source_codepoints']; x,y = m['fragment_codepoints']
        assert before['document']['text'][a:b] == doc['text'][x:y]


def test_adjacent_typed_origins_and_unicode_are_not_trimmed_or_separated():
    c = case('unicode'); doc = typed_fragments(c['record'])['document']
    assert doc['text'] == c['record']['document']['text'][2:]
    assert 'e\u0301' in doc['text'] and '\r\n\r\n' in doc['text']
    assert doc['fragmentConstruction']['synthetic_separator_codepoints'] == 0
    for m in doc['fragmentConstruction']['mappings']:
        assert m['source_codepoints'][0] == m['fragment_codepoints'][0] + 2


@pytest.mark.parametrize('text', ['model words only', ''])
def test_no_typed_source_is_explicitly_unsupported(text):
    record = final_document([event(0, doc=text)], dict(writer='w',session='s',prompt='p'))
    result = typed_fragments(record)
    assert result['status'] == 'unsupported-no-typed-words' and result['document'] is None
    assert result['support']['typed_codepoints'] == 0


def test_fresh_serialized_join_and_fragment_reconstruction():
    code = ('import json,sys;from runners.drive.engine_export_join import join_exports,typed_fragments;'
        'c=json.load(open(sys.argv[1],encoding="utf8"))["cases"];'
        'print(json.dumps([[join_exports(x["rows"],[x["record"]],[x["export"]]),typed_fragments(x["record"])] for x in c],sort_keys=True))')
    child = subprocess.run([sys.executable, '-X','utf8','-B','-c',code,str(FIXTURE)],
        capture_output=True,text=True,encoding='utf8',timeout=30,
        env={**os.environ,'PYTHONHASHSEED':'619'},
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode == 0, child.stderr
    cases = json.loads(FIXTURE.read_text(encoding='utf8'))['cases']
    assert json.loads(child.stdout) == [[run(c),typed_fragments(c['record'])] for c in cases]
