"""Known raw records, sealed payload sentinels and source/producer substitutions."""
import copy
import csv
import json
from pathlib import Path
import zipfile

import pytest

from runners.stage9 import closure_external_raw as subject
from runners.stage9 import common
from runners.stage9.broll import partition
from runners.stage9.commitbench import PIN


@pytest.mark.parametrize('value', [[], {}, ['a}b', {'nested': [1, 'quote"\\end', '\u2603']}],
    {'a': 'x,y', 'nested': {'braces': '[{}]'}, 'n': None}, {'array': [True, False, -2.5]}])
def test_json_fragments_preserve_escaped_nested_values(value):
    encoded = json.dumps(value, ensure_ascii=True, indent=2)
    if isinstance(value, dict):
        assert {k: json.loads(v) for k, v in subject.fragments(encoded)} == value
    else:
        assert [json.loads(v) for v in subject.fragments(encoded, False)] == value


@pytest.mark.parametrize('encoded', ['{"a":1,"a":2}', '{"a":1,}', '{"a":}',
    '{"a":[1}', '{"a":"unterminated}', '{"a" 1}', '{"a":1} {}'])
def test_json_fragments_refuse_ambiguous_or_incomplete_boundaries(encoded):
    with pytest.raises(ValueError): list(subject.fragments(encoded))


def page_fixture(tmp_path):
    rows = []
    for i in range(100):
        row = {'hash': str(i), 'project': 'project-'+str(i), 'split': 'train', 'diff_languages': 'Python',
            'diff': 'SELECTED [braces] "quote" \\ path\n\u2603' if i == 17 else 'SEALED DIFF',
            'message': 'selected complete description' if i == 17 else 'SEALED DESCRIPTION'}
        rows.append({'row_idx': 400+i, 'row': row, 'truncated_cells': []})
    body = {'partial': False, 'num_rows_total': 9000, 'rows': rows}
    path = tmp_path/'page.json'; page = {'offset': 400, 'headers': {'X-Revision': PIN},
        'receipt': {'sha256': None, 'complete_eof': True}}
    return path, page, body


def save_page(path, page, body):
    path.write_text(json.dumps(body, ensure_ascii=True), encoding='utf-8')
    page['receipt']['sha256'] = common.file_hash(path)


def test_only_selected_api_payload_is_decoded(tmp_path, monkeypatch):
    path, page, body = page_fixture(tmp_path); save_page(path, page, body)
    wanted = common.digest({'commit': '17', 'project': 'project-17'})
    original = subject.json.loads; decoded = []
    def guarded(value, *args, **kwargs):
        assert 'SEALED' not in value
        if value.lstrip().startswith('{'): decoded.append(value)
        return original(value, *args, **kwargs)
    monkeypatch.setattr(subject.json, 'loads', guarded)
    rows, inventory = subject.selected_page(path, page, 9000, {wanted})
    assert rows == {wanted: body['rows'][17]['row']}
    assert len(inventory) == len(set(inventory)) == 100
    assert len(decoded) == 1


@pytest.mark.parametrize('fault', ['partial', 'total', 'count', 'offset', 'index', 'truncated',
    'revision', 'eof', 'schema', 'split', 'source_hash', 'duplicate_key'])
def test_api_source_guards(tmp_path, fault):
    path, page, body = page_fixture(tmp_path)
    if fault == 'partial': body['partial'] = True
    if fault == 'total': body['num_rows_total'] += 1
    if fault == 'count': body['rows'].pop()
    if fault == 'offset': page['offset'] += 1
    if fault == 'index': body['rows'][99]['row_idx'] = 498
    if fault == 'truncated': body['rows'][0]['truncated_cells'] = ['diff']
    if fault == 'revision': page['headers']['X-Revision'] = 'other'
    if fault == 'eof': page['receipt']['complete_eof'] = False
    if fault == 'schema': body['rows'][0]['row']['extra'] = 'not declared'
    if fault == 'split': body['rows'][0]['row']['split'] = 'test'
    if fault == 'duplicate_key': body['rows'][18]['row'] = copy.deepcopy(body['rows'][17]['row'])
    save_page(path, page, body)
    if fault == 'source_hash': path.write_text(path.read_text()+' ', encoding='utf-8')
    wanted = common.digest({'commit': '17', 'project': 'project-17'})
    with pytest.raises(ValueError): subject.selected_page(path, page, 9000, {wanted})


@pytest.fixture
def broll_fixture(tmp_path, monkeypatch):
    real_repo = subject.REPO
    root = tmp_path/'results'; prepared = root/'private/prepared/broll'; archive = root/'private/archive'; cases = root/'private/cases'
    monkeypatch.setattr(subject, 'REPO', tmp_path); monkeypatch.setattr(subject, 'ROOT', root)
    monkeypatch.setattr(common, 'REPO', tmp_path)
    def inside(path, base=None):
        path, base = Path(path).resolve(), Path(base or root).resolve()
        if not path.is_relative_to(base) or path == base: raise ValueError('outside fixture boundary')
        return path
    monkeypatch.setattr(subject, 'inside', inside)
    for name in ('broll.py', 'common.py'):
        relative = Path('runners/stage9')/name
        for destination in (tmp_path/relative, archive/relative):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((real_repo/relative).read_bytes())
    code = common.closure([tmp_path/'runners/stage9/broll.py', tmp_path/'runners/stage9/common.py'])
    common.write(archive/'SOURCE.json', code)
    raw = tmp_path/'csv'; raw.mkdir()
    def csv_file(name, fields, rows):
        with (raw/name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    scripts = {f's{i}': {'script': 'Alpha beta', 'topic': 'example', 'tokens': ['Alpha', 'beta'],
        'support': ['alpha', 'beta'], 'word_counts': {'alpha': 1, 'beta': 1},
        'pos': {'alpha': 'NOUN', 'beta': 'VERB'}, 'source_words': 2, 'source_unique_words': 2} for i in range(12)}
    csv_file('df_scripts_cleaned.csv', ['object','script','video_type','word_lists','unique_words','Nwords','Nunique_words'],
        [{'object': key, 'script': 'Alpha beta', 'video_type': 'example', 'word_lists': "['Alpha', 'beta']",
          'unique_words': "['Alpha', 'beta']", 'Nwords': 2, 'Nunique_words': 2} for key in scripts])
    csv_file('broll_transcript_vocab.csv', ['object','word','type'],
        [{'object': key, 'word': word, 'type': pos} for key in scripts for word,pos in [('alpha','NOUN'),('beta','VERB')]])
    people = [common.digest({'broll-person': f'p{i}'})[:24] for i in range(12)]
    allocation = partition(people, people[:2]); script_split = partition(scripts, {'s0'}, 'broll-script-v1')
    csv_file('broll_alldata_vocab.csv', ['gameID','object'], [{'gameID':'p1','object':'s0'}])
    rows = []; expected = []
    for i, person in enumerate(people):
        for trial in range(12):
            goal = 'informative' if i % 2 else 'entertaining'; key = f's{trial}'
            chosen = [] if trial == 0 else ['outside'] if trial == 2 else ['alpha']
            highlights = [] if trial == 0 else [{'highlight_index': 0, 'words': chosen}]
            response = '{}' if trial == 0 else "{'0': {'0': 'outside'}}" if trial == 2 else "{'0': {'0': 'Alpha!!'}}"
            if allocation[person] != 'development': response = 'SEALED RESPONSE: DO NOT LITERAL DECODE'
            rows.append({'gameID': f'p{i}', 'object': key, 'trialNum': trial, 'goal': goal, 'eventType': 'test', 'response': response})
            if allocation[person] == 'development':
                reason = 'selected fragment outside script vocabulary' if trial == 2 else None
                expected.append({'key': common.digest({'person':person,'trial':trial,'script':key})[:24],
                    'person':person, 'script_key':key, 'trial':trial, 'goal':goal, 'highlights':highlights,
                    'selected_words':chosen, 'labels':[int('alpha' in chosen),0], 'usable':reason is None,
                    'exclusion':reason, 'unmatched_word_count':int(trial == 2)})
    csv_file('broll_alldata.csv', ['gameID','object','trialNum','goal','eventType','response'], rows)
    blob = tmp_path/'archive.zip'
    with zipfile.ZipFile(blob, 'w') as z:
        for p in raw.iterdir(): z.writestr(p.name, p.read_bytes())
    sha = common.file_hash(blob); actual_raw = root/'private/intake/materialized'/sha; actual_raw.mkdir(parents=True)
    for p in raw.iterdir(): (actual_raw/p.name).write_bytes(p.read_bytes())
    target = root/'private/intake/objects'/sha; target.parent.mkdir(parents=True); target.write_bytes(blob.read_bytes())
    source = {'sha256':sha,'complete_eof':True}; rights = {'archive_sha256':sha,'private_research_analysis_accepted':True}
    chronology = {'fixture':'independently specified twelve presentation indices'}
    for name, value in [('BROLL_ARCHIVE',source),('BROLL_REUSE_REVIEW',rights),('BROLL_TASK_SOURCE',chronology)]:
        common.write(root/'intake'/(name+'.json'), value)
    identity = {'sources':code,'source':source,'reuse_review':rights,'chronology_source':chronology,
        'files':{p.name:common.file_hash(p) for p in actual_raw.iterdir() if p.name!='broll_alldata_vocab.csv'},
        'person_split':allocation,'script_split':script_split}
    common.write(prepared/'IDENTITY.json',identity); common.write(prepared/'SCRIPTS.json',scripts)
    common.write(prepared/'development.json',expected)
    common.write(prepared/'reserve.json',{'opaque':'not a usable prepared response'})
    common.write(prepared/'COMPLETE.json',{'identity_sha256':common.digest(identity),'people':12,'attempted_records':144,
        'person_split_counts':dict(__import__('collections').Counter(allocation.values())),
        'script_split_counts':dict(__import__('collections').Counter(script_split.values()))})
    common.write(cases/'CASES.json',{'projection':'separately validated by closure_cases'})
    fixture = prepared, archive, cases, actual_raw
    resign_broll(fixture)
    return fixture


def resign_broll(fixture):
    prepared, archive, cases, raw = fixture
    metadata = {'canonical_identity_sha256': common.digest(common.read(prepared/'IDENTITY.json')),
        'reserve_records_parsed':False,'source_files':{str(prepared/n):common.file_hash(prepared/n) for n in ('SCRIPTS.json','development.json')}}
    common.write(cases/'METADATA.json',metadata)
    identity = {'operation':'broll-cases-v1','scope':'pilot','metadata_sha256':common.digest(metadata)}
    common.write(cases/'IDENTITY.json',identity)
    common.write(cases/'COMPLETE.json',{'identity_sha256':common.digest(identity),'execution_complete':True,
        'outputs':common.closure([cases/'CASES.json',cases/'METADATA.json'])})


def test_consumed_broll_known_words_empty_exclusions_and_sealed_responses(broll_fixture):
    prepared, archive, cases, raw = broll_fixture; before = common.closure([prepared,cases,raw])
    report = subject.inspect_broll(prepared,archive,cases)
    expected = common.read(prepared/'development.json')
    assert report['raw_responses_decoded'] == len(expected) == 24
    assert sum(not r['selected_words'] for r in expected) == 2
    assert sum(not r['usable'] for r in expected) == 2
    assert report['participant_identity_records'] == 144 and report['scripts'] == 12
    assert report['unselected_raw_responses_decoded'] == report['new_reserve_openings'] == 0
    assert common.closure([prepared,cases,raw]) == before


@pytest.mark.parametrize('field,value', [('labels',[0,1]),('selected_words',['beta']),('trial',99),
    ('highlights',[]),('exclusion','invented'),('unmatched_word_count',100)])
def test_broll_rehashed_consumed_record_changes_refuse(broll_fixture,field,value):
    prepared, archive, cases, raw = broll_fixture
    rows=common.read(prepared/'development.json');rows[1][field]=value
    common.write(prepared/'development.json',rows);resign_broll(broll_fixture)
    with pytest.raises(ValueError,match='do not reconstruct'): subject.inspect_broll(prepared,archive,cases)


def test_broll_changed_raw_archive_refuses(broll_fixture):
    prepared, archive, cases, raw = broll_fixture
    (raw/'broll_alldata.csv').write_bytes(b'changed')
    with pytest.raises(ValueError,match='materialized'): subject.inspect_broll(prepared,archive,cases)


def test_broll_reserve_input_path_cannot_enter_audit(broll_fixture):
    prepared, archive, cases, raw = broll_fixture
    metadata=common.read(cases/'METADATA.json')
    metadata['source_files'][str(prepared/'reserve.json')]=common.file_hash(prepared/'reserve.json')
    common.write(cases/'METADATA.json',metadata)
    identity=common.read(cases/'IDENTITY.json');identity['metadata_sha256']=common.digest(metadata)
    common.write(cases/'IDENTITY.json',identity)
    complete=common.read(cases/'COMPLETE.json');complete['identity_sha256']=common.digest(identity)
    complete['outputs']=common.closure([cases/'CASES.json',cases/'METADATA.json']);common.write(cases/'COMPLETE.json',complete)
    with pytest.raises(ValueError,match='cannot widen'): subject.inspect_broll(prepared,archive,cases)
