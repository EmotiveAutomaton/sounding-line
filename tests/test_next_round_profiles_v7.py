import copy
import json
import pytest
from runners.next_round import profiles_v7 as p


def message(obj=None):
    return {'stop_reason': 'end_turn', 'model': p.api.MODELS['RS'],
            'usage': {'input_tokens': 1200, 'output_tokens': 80},
            'content': [{'type': 'text', 'text': json.dumps(obj or {'preferences': [
                {'statement': 'Often edits offered continuations.', 'evidence_indices': [0]}]})}]}


@pytest.mark.parametrize('bad', [
    {'preferences': []}, {'preferences': [{'statement': ' '.join(['word']*25), 'evidence_indices': [0]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [True]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [2]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [0, 0]}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': []}]},
    {'preferences': [{'statement': 'x', 'evidence_indices': [0]}], 'future': 'x'},
])
def test_bad_profiles(bad):
    with pytest.raises(ValueError): p.parse(message(bad), 2)


def test_duplicate_json_and_truncation():
    m = message(); m['content'][0]['text'] = '{"preferences":[],"preferences":[]}'
    with pytest.raises(ValueError): p.parse(m, 2)
    m = message(); m['stop_reason'] = 'max_tokens'
    with pytest.raises(ValueError): p.parse(m, 2)
    assert len(p.parse(message(), 2)['preferences']) == 1


def test_whole_lifecycle_and_reentry(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    row = {'custom_id': 'known', 'params': {'model': p.api.MODELS['RS'], 'max_tokens': 1500},
           'reader': 'RS', 'history_records': 2}
    monkeypatch.setattr(p, 'rows_for', lambda phase: [copy.deepcopy(row)])
    calls = []
    def transport(path, body=None):
        calls.append((path, body))
        if path.startswith('/v1/models/'): return json.dumps({'id': p.api.MODELS['RS']}).encode()
        if path.endswith('count_tokens'): return b'{"input_tokens":1200}'
        if path == '/v1/messages/batches': return b'{"id":"fixture_batch"}'
        if path.endswith('/results'):
            return json.dumps({'custom_id': 'known', 'result': {'type': 'succeeded', 'message': message()}}).encode()
        return b'{"id":"fixture_batch","processing_status":"ended"}'
    monkeypatch.setattr(p.api, 'request', transport)
    # A scratch root still needs repo-relative pins; substitute only this test's root.
    monkeypatch.setattr(p, 'REPO', p.REPO)
    monkeypatch.setattr(p, 'prepare', p.prepare)
    folder = tmp_path/'canary'
    p.freeze(folder/'REQUESTS.json', [row])
    p.freeze(folder/'PLAN.json', {'at': p.time.time(), 'source_pins': {}, 'request_digest': p.digest([row]),
                               'reserved_cents': 4, 'max_seconds': 86400})
    reservations = []
    def reserve(*args): reservations.append(args); return {'reserved_cents': args[2]}
    monkeypatch.setattr(p.budget, 'reserve', reserve)
    monkeypatch.setattr(p.budget, 'reconcile_tokens', lambda *args: None)
    p.submit('canary')
    with pytest.raises(ValueError): p.submit('canary')
    assert len(reservations) == 1
    assert len([c for c in calls if c[0] == '/v1/messages/batches']) == 1
    first = p.retrieve('canary'); count = len(calls)
    assert first['valid'] == first['attempted'] == 1
    assert p.replay('canary') == first
    assert p.reconcile('canary')['status'] == 'RECONCILED'
    assert len(calls) == count
    result = folder/'RESULTS.jsonl'
    result.write_text(result.read_text()+'\n'+result.read_text(), encoding='utf8')
    with pytest.raises(ValueError): p.replay('canary')


def test_uncertain_submit_retains_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    folder = tmp_path/'canary'; rows = [{'custom_id': 'fixture', 'params': {}}]
    p.freeze(folder/'REQUESTS.json', rows)
    p.freeze(folder/'PLAN.json', {'at': p.time.time(), 'source_pins': {}, 'request_digest': p.digest(rows),
                               'reserved_cents': 2, 'max_seconds': 86400})
    monkeypatch.setattr(p.budget, 'reserve', lambda *a: {'reserved_cents': 2})
    def fail(*args): raise TimeoutError()
    monkeypatch.setattr(p.api, 'request', fail)
    with pytest.raises(TimeoutError): p.submit('canary')
    assert p.read(folder/'UNKNOWN.json')['reservation_retained']
    with pytest.raises(ValueError): p.submit('canary')


def test_real_request_separation():
    pilot, main = p.rows_for('pilot'), p.rows_for('main')
    assert len(pilot) == 6 and len(main) == 62
    assert not {r['writer'] for r in pilot} & {r['writer'] for r in main}
    for r in pilot+main:
        assert set(json.loads(r['params']['messages'][0]['content'])) == {'history'}
        assert r['params']['max_tokens'] == 1500
        assert r['params']['output_config']['format']['schema'] == p.schema_for(r['history_records'])


@pytest.mark.parametrize('words,valid', [(0, False), (1, True), (24, True), (25, False)])
def test_exact_word_bound(words, valid):
    text = ' '.join(['word']*words)
    m = message({'preferences': [{'statement': text, 'evidence_indices': [0]}]})
    if valid:
        assert p.parse(m, 1)['preferences'][0]['statement'] == text
    else:
        with pytest.raises(ValueError): p.parse(m, 1)


@pytest.mark.parametrize('text', [' two', 'two ', 'two  words', 'two\twords',
                                  'two\nwords', 'two\u00a0words', 'two\u2003words', 'word\n'])
def test_original_whitespace_contract_unchanged(text):
    from runners.next_round import profiles as old
    m = message({'preferences': [{'statement': text, 'evidence_indices': [0]}]})
    assert p.parse(m, 1) == old.parse(m, 1)


def test_same_evidence_and_original_gate():
    from runners.next_round import profiles as old
    for phase in ['pilot', 'main']:
        before, after = old.rows_for(phase), p.rows_for(phase)
        for a, b in zip(before, after):
            for key in ['writer', 'arm', 'history_records', 'evidence_sha256']:
                assert a[key] == b[key]
            history = json.loads(b['params']['messages'][0]['content'])['history']
            assert [r.pop('record_index') for r in history] == list(range(len(history)))
            assert history == json.loads(a['params']['messages'][0]['content'])['history']
            assert a['custom_id'] != b['custom_id']
    # New accepted representation remains acceptable under the unchanged old gate.
    for n in range(1, 25):
        m = message({'preferences': [{'statement': ' '.join(['w']*n), 'evidence_indices': [0]}]})
        assert p.parse(m, 1) == old.parse(m, 1)


@pytest.mark.parametrize('defect', ['invalid', 'usage', 'landing', 'pins'])
def test_main_refuses_before_reservation(tmp_path, monkeypatch, defect):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    monkeypatch.setattr(p, 'validate_plan', lambda root: {'at': p.time.time()})
    pilot = {'attempted': 6, 'valid': 5 if defect == 'invalid' else 6,
             'usage_complete': defect != 'usage'}
    monkeypatch.setattr(p, 'replay', lambda phase: pilot)
    p.freeze(tmp_path/'pilot/COMPLETE.json', pilot)
    p.freeze(tmp_path/'pilot/LANDED.json', {
        'complete_sha256': p.filehash(tmp_path/'pilot/COMPLETE.json'),
        'full_write_through': defect != 'landing'})
    monkeypatch.setattr(p.budget, 'reserve', lambda *a: pytest.fail('must refuse before reserve'))
    with pytest.raises(ValueError): p.submit('main')


def test_supervisor_registers_before_post(tmp_path, monkeypatch):
    from runners.next_round import profile_supervisor_v7 as s
    monkeypatch.setattr(s, 'REPO', tmp_path)
    monkeypatch.setattr(p, 'ROOT', tmp_path/'raw')
    native = {'pid': 123, 'creation_time': 456}
    monkeypatch.setattr(s, 'native_identity', lambda: native)
    monkeypatch.setattr(p, 'validate_plan', lambda root: {'max_seconds': 86400})
    p.freeze(tmp_path/'.agent-state/watch.json', {'process_watches': [], 'paths': []})
    def submit(phase):
        cfg = p.read(tmp_path/'.agent-state/watch.json')
        assert cfg['process_watches'][0]['native'] == native
        assert 'raw/pilot/UNKNOWN.json' in cfg['paths']
        p.freeze(p.ROOT/phase/'SUBMITTED.json', {'at': p.time.time()})
    monkeypatch.setattr(p, 'submit', submit)
    monkeypatch.setattr(p, 'retrieve', lambda phase: {'status': 'COMPLETE'})
    monkeypatch.setattr(p, 'reconcile', lambda phase: None)
    s.worker('pilot')
    assert p.read(p.ROOT/'pilot/EXIT.json')['status'] == 'COMPLETE'


def test_canary_is_synthetic_and_largest_reference_grammar():
    row, = p.rows_for('canary')
    assert row['writer']=='synthetic' and row['history_records']==32
    history=json.loads(row['params']['messages'][0]['content'])['history']
    assert [r['record_index'] for r in history]==list(range(32))
    assert all('fictional fox' in r['draft_end'] for r in history)
    assert max(r['history_records'] for r in p.rows_for('pilot')+p.rows_for('main'))<=32
    assert row['params']['output_config']['format']['schema']==p.schema_for(32)
    assert row['params']['max_tokens']==1500


@pytest.mark.parametrize('phase,prereq,n', [('pilot','canary',1),('main','pilot',6)])
@pytest.mark.parametrize('tampered', [False,True])
def test_actual_transition_and_changed_proof(tmp_path,monkeypatch,phase,prereq,n,tampered):
    monkeypatch.setattr(p,'ROOT',tmp_path)
    proof=tmp_path/prereq/'VERIFICATION.json'; p.freeze(proof,{'checked':True})
    pins={proof.relative_to(p.REPO).as_posix():p.filehash(proof)}
    complete={'attempted':n,'valid':n,'usage_complete':True}
    p.freeze(tmp_path/prereq/'COMPLETE.json',complete)
    p.freeze(tmp_path/prereq/'LANDED.json',{'complete_sha256':p.filehash(tmp_path/prereq/'COMPLETE.json'),
        'full_write_through':True,'verification_pins':pins,'write_through_pins':pins})
    if tampered:proof.write_text('{"checked":false}',encoding='utf8')
    monkeypatch.setattr(p,'replay',lambda phase:complete)
    row={'custom_id':'known','params':{}}
    p.freeze(tmp_path/phase/'REQUESTS.json',[row])
    p.freeze(tmp_path/phase/'PLAN.json',{'at':p.time.time(),'source_pins':{},'request_digest':p.digest([row]),'reserved_cents':2,'max_seconds':86400})
    calls=[]
    monkeypatch.setattr(p.budget,'reserve',lambda *a:calls.append(a) or {'reserved_cents':2})
    monkeypatch.setattr(p.api,'request',lambda *a:b'{"id":"fixture"}')
    if tampered:
        with pytest.raises(ValueError):p.submit(phase)
        assert calls==[]
    else:
        p.submit(phase)
        assert len(calls)==1
        assert calls[0][1]==('P' if phase=='pilot' else 'M-API')
        with pytest.raises(ValueError):p.submit(phase)


def test_exact_original_schema_and_validator():
    from runners.next_round import profiles as old
    assert p.SCHEMA == old.SCHEMA
    assert p.parse is old.parse and p.strict_json is old.strict_json
    assert '8 to 12 words' in p.SYSTEM and 'hard maximum of 24' in p.SYSTEM
    assert 'pattern' not in json.dumps(p.schema_for(32))


@pytest.mark.parametrize('phase', ['pilot', 'main'])
@pytest.mark.parametrize('defect', ['invalid', 'usage', 'landing', 'pins'])
def test_prepare_refuses_egress_before_admission(tmp_path, monkeypatch, phase, defect):
    monkeypatch.setattr(p, 'ROOT', tmp_path)
    prior, n = ('canary', 1) if phase == 'pilot' else ('pilot', 6)
    complete = {'attempted': n, 'valid': n-1 if defect=='invalid' else n, 'usage_complete': defect!='usage'}
    monkeypatch.setattr(p, 'replay', lambda phase: complete)
    p.freeze(tmp_path/prior/'COMPLETE.json', complete)
    p.freeze(tmp_path/prior/'LANDED.json', {'complete_sha256': p.filehash(tmp_path/prior/'COMPLETE.json'),
        'full_write_through': defect!='landing'})
    monkeypatch.setattr(p.api, 'request', lambda *a: pytest.fail('no egress before prerequisite'))
    with pytest.raises(ValueError): p.prepare(phase)
    assert not (tmp_path/phase).exists()


@pytest.mark.parametrize('count',[1,16,23,32])
def test_reference_schema_and_original_rejection(count):
    schema=p.schema_for(count)
    assert schema['properties']['preferences']['items']['properties']['evidence_indices']['items']['enum']==list(range(count))
    good=message({'preferences':[{'statement':'The fox stayed.', 'evidence_indices':[count-1]}]})
    assert p.parse(good,count)
    bad=message({'preferences':[{'statement':'The fox stayed.', 'evidence_indices':[count]}]})
    with pytest.raises(ValueError):p.parse(bad,count)


def test_schema_visible_and_no_source_mutation():
    from runners.next_round import profiles as old
    original=copy.deepcopy(old.SCHEMA)
    for row in p.rows_for('pilot')+p.rows_for('main')+p.rows_for('canary'):
        assert json.loads(row['params']['system'].split('Schema: ',1)[1])==row['params']['output_config']['format']['schema']
    assert old.SCHEMA==original
    for count in [0,33,True]:
        with pytest.raises(ValueError):p.schema_for(count)


@pytest.mark.parametrize('stop', ['end_turn', 'max_tokens'])
def test_valid_json_prefix_never_salvaged(stop):
    m=message()
    m['content'][0]['text'] += '\n\nEvidence\nOutput after the object.'
    m['stop_reason']=stop
    with pytest.raises(ValueError): p.parse(m,2)


@pytest.mark.parametrize('text', ['', ' ', '\t\n', '\u00a0'])
def test_no_relaxed_empty_statement_acceptance(text):
    m=message({'preferences':[{'statement':text,'evidence_indices':[0]}]})
    with pytest.raises(ValueError): p.parse(m,1)


def test_only_pattern_removed_from_v6_wire():
    from runners.next_round import profiles_v6 as old
    for phase in ['canary','pilot','main']:
        for a,b in zip(old.rows_for(phase),p.rows_for(phase)):
            assert a['params']['messages']==b['params']['messages']
            assert a['params']['system'].split('Schema: ',1)[0]==b['params']['system'].split('Schema: ',1)[0]
            assert a['evidence_sha256']==b['evidence_sha256']
            schema=copy.deepcopy(a['params']['output_config']['format']['schema'])
            fields=schema['properties']['preferences']['items']['properties']
            assert fields['statement'].pop('pattern')==r'[^\s]'
            assert schema==b['params']['output_config']['format']['schema']
            assert schema['properties']['preferences']['minItems']==1
            assert fields['evidence_indices']['minItems']==1
            assert a['params']['model']==b['params']['model']
            assert a['params']['max_tokens']==b['params']['max_tokens']==1500
            assert b['custom_id']!=a['custom_id']
    assert p.parse is old.parse and p.strict_json is old.strict_json
