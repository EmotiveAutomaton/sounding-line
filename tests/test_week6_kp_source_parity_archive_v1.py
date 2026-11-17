"""Constructed controls only: never run against human rows or live identities.

Includes the original nested D33/KP loader code, actual stage execute/replay,
and actual capsule consumer. Only the historical source constructor and native
observations are invented. This is not a native qualification receipt.
"""
from pathlib import Path
from types import SimpleNamespace
import copy
import gzip
import hashlib
import json
import math
import pytest

from runners.drive.cards import week6_kp_source_parity_archive_v1 as archive
from runners.drive.cards import week6_kp_source_stage_parity_archive_v1 as stage
from runners.drive.cards import week6_kp_capsule_source_parity_archive_v1 as capsule
from runners.drive.cards import week6_kp_riders_capsule_parity_archive_v1 as rider
from runners.drive.cards import week6_kp_source_stage_v1 as old_stage
from runners.drive.cards import week6_kp_riders_capsule_v1 as old_rider
from runners.drive.cards import timing_d33_calibrated as d33
from runners.drive.cards.timing_d33_supported_stats import NAMES


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stage.canonical(value))


def resolver_fixture(tmp_path):
    target = tmp_path/'denied'/'PARITY.json'
    target.parent.mkdir()
    payload = (json.dumps({'invented': True, 'matching_equal': True}, sort_keys=True)+'\n').encode()
    target.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    entry = dict(path=str(target), sha256=expected, receipt=json.loads(payload))
    first, second = tmp_path/'first.json', tmp_path/'second.json'
    write(first, {'parity': entry})
    write(second, {'tests': {'receipt': {'parity': entry}}})
    anchors = [(first, archive.digest(first), ('parity',)),
               (second, archive.digest(second), ('tests','receipt','parity'))]
    def denied(path):
        if archive.path_key(path) == archive.path_key(target):
            raise PermissionError(13, 'constructed access denial', str(path))
        return archive.digest(path)
    resolver = archive.ExactParityResolver(target, expected, anchors, denied)
    return resolver, target, expected


def test_exact_archived_original_bytes(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    r.check_files({str(target): expected})
    assert r.evidence()['original_bytes'] == len(target.read_bytes())


def test_changed_original_expected_digest_refuses(tmp_path):
    r, target, _ = resolver_fixture(tmp_path)
    with pytest.raises(ValueError, match='pin changed'):
        r.check_files({str(target): '0'*64})


def test_missing_original_is_not_a_permission_exception(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    target.unlink(); r.filehash = archive.digest
    with pytest.raises(FileNotFoundError): r.check_files({str(target): expected})


def test_other_denied_path_cannot_use_archive(tmp_path):
    r, _, expected = resolver_fixture(tmp_path)
    def denied(path): raise PermissionError(13, 'constructed', str(path))
    r.filehash = denied
    with pytest.raises(PermissionError): r.check_files({str(tmp_path/'other'): expected})


def test_other_io_failure_propagates(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    def other(path): raise OSError(5, 'constructed I/O failure')
    r.filehash = other
    with pytest.raises(OSError): r.check_files({str(target): expected})


def test_unknown_permission_error_propagates(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    def unknown(path): raise PermissionError(1, 'constructed unknown refusal')
    r.filehash = unknown
    with pytest.raises(PermissionError): r.check_files({str(target): expected})


def test_readable_changed_original_is_not_hidden(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    target.write_bytes(b'changed'); r.filehash = archive.digest
    with pytest.raises(ValueError, match='Frozen source/input changed'):
        r.check_files({str(target): expected})


def test_changed_anchor_bytes_refuse(tmp_path):
    r, _, _ = resolver_fixture(tmp_path)
    r.anchors[0][0].write_bytes(b'{}')
    with pytest.raises(ValueError, match='anchor pin'): r.evidence()


@pytest.mark.parametrize('field', ['path','sha256','receipt'])
def test_wrong_embedded_record_refuses(tmp_path, field):
    r, _, _ = resolver_fixture(tmp_path)
    path, _, route = r.anchors[1]
    value = json.loads(path.read_bytes()); entry = value['tests']['receipt']['parity']
    entry[field] = {'invented': 'changed'} if field == 'receipt' else 'wrong'
    write(path, value)
    r.anchors = (r.anchors[0], (path, archive.digest(path), route))
    with pytest.raises(ValueError): r.evidence()


def test_both_preserved_anchors_required(tmp_path):
    r, _, _ = resolver_fixture(tmp_path); r.anchors = r.anchors[:1]
    with pytest.raises(ValueError): r.evidence()


def test_unrelated_frozen_pin_stays_enforced(tmp_path):
    r, target, expected = resolver_fixture(tmp_path)
    other = tmp_path/'other'; other.write_bytes(b'original'); pin = archive.digest(other)
    other.write_bytes(b'changed')
    with pytest.raises(ValueError): r.check_files({str(target): expected, str(other): pin})


def test_original_validator_globals_are_not_mutated(tmp_path):
    r, _, _ = resolver_fixture(tmp_path)
    validator = d33.load_source.__globals__['check_files']
    source_view = archive.original.load_authenticated.__globals__['d33']
    local = archive.isolated_loader(r)
    assert local.__code__ is archive.original.load_authenticated.__code__
    assert local.__globals__['d33'].load_source.__code__ is d33.load_source.__code__
    assert local.__globals__['d33'].load_source.__globals__['check_files'] == r.check_files
    assert d33.load_source.__globals__['check_files'] is validator
    assert archive.original.load_authenticated.__globals__['d33'] is source_view


def world(tmp_path, monkeypatch):
    """Invented one-word raw source, no mocked KP transform or roster selector."""
    r, target, expected = resolver_fixture(tmp_path)
    old_roster = dict(retained_keys=[['S',0]], unsupported_keys=[], coverage={}, writers={
        'W': dict(calibration_keys=[['S',0]], retained_evaluation_words=1,
                  unsupported_evaluation_words=0,
                  supported_sessions=dict(calibration=['S'],evaluation=['S']),
                  unsupported_sessions=dict(calibration=[],evaluation=[]))})
    raw = tmp_path/'invented.jsonl'
    events = [dict(eventName='system-initialize',eventTimestamp=1000,currentDoc=''),
              dict(eventName='text-insert',eventTimestamp=2000,eventSource='user',
                   textDelta={'ops':[{'insert':'alpha '}]})]
    raw.write_text(''.join(json.dumps(x)+'\n' for x in events), encoding='utf8', newline='\n')
    raw_pin = archive.digest(raw)
    word = dict(index=0,ordinal=1,is_word=True,token='alpha',seconds=2.,
                population_probability=.5,context=[])
    row = {name: 0. for name in NAMES if name != 'intercept'}
    row.update(writer='W',session='S',index=0,log_pause=1.)
    class InventedSources:
        def roster_for(self, variant):
            assert variant == 'pair'
            return copy.deepcopy(old_roster)
    def constructor(obj, values):
        assert set(values) == d33.original.INPUTS
        obj.saved = {'rows':[dict(writer='W',session='S',index=0)]}
        obj.lookup = {'S':dict(writer='W',session='S',timestamp=1.,end_at=3.,words=[word])}
        obj.units = {'pair':{'S':{'proof':dict(supported=True,own_sessions=[],
            donor_sessions=[],trim_allocations=[],before=1.)}}}
        obj.raw = SimpleNamespace(root=tmp_path, raw={'S':{'path':raw.name}},
            session=lambda sid: {'source_hashes':{'raw':raw_pin}})
    original_load = archive.isolated_loader
    local_d33 = SimpleNamespace(**dict(vars(d33), load_source=archive.copied(d33.load_source,
        sources=SimpleNamespace(Sources=InventedSources),
        counts=SimpleNamespace(__name__=d33.counts.__name__,source_constructor=constructor))))
    monkeypatch.setattr(archive, 'resolver', lambda: r)
    monkeypatch.setattr(archive, 'LOADER_PINS', {})
    monkeypatch.setattr(archive, 'isolated_loader', lambda receipt_resolver:
        original_load(receipt_resolver, d33_template=local_d33))
    prior = tmp_path/'prior'; prior.mkdir()
    write(prior/'PLAN.json',dict(module=d33.counts.__name__,config=d33.original.configuration('pair'),
        inputs={key:'constructed-unopened' for key in d33.original.INPUTS},
        pins={str(target):expected}))
    write(prior/'output/SUPPORTED_ROSTER.json',old_roster)
    write(prior/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={name:archive.digest(prior/name) for name in ('PLAN.json','output/SUPPORTED_ROSTER.json')}))
    receipt = tmp_path/'prior_receipt.json'
    write(receipt,dict(complete_sha256=archive.digest(prior/'COMPLETE.json'),
        plan_sha256=archive.digest(prior/'PLAN.json'),full_fresh_source_verification=True,
        state='invalid',reason='retained evaluation writers have no supported calibration words'))
    root = tmp_path/'calibrated'
    write(root/'PLAN.json',dict(module='runners.drive.cards.timing_d33_calibrated',config=d33.CONFIG,
        inputs=dict(prior_completion=str(prior/'COMPLETE.json'),prior_receipt=str(receipt))))
    selected = d33.select_population(old_roster,{'rows':[row]})
    write(root/'output/SUPPORTED_ROSTER.json',selected)
    write(root/'output/CALIBRATION.json',{'W':{'alpha':{'own':0.}}})
    write(root/'output/PRIMARY.json',{'statistics':{'point_fits':{'primary':
        {'coefficients':{'intercept':0.},'variance_ratio':0.}}}})
    (root/'output/DESIGN.json.gz').write_bytes(gzip.compress(stage.canonical([row]),mtime=0))
    names=('PLAN.json','output/SUPPORTED_ROSTER.json','output/CALIBRATION.json',
           'output/PRIMARY.json','output/DESIGN.json.gz')
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={name:archive.digest(root/name) for name in names}))
    qualification=tmp_path/'qualification.json'
    write(qualification,dict(status='COMPLETE',qualification_status='passed',expected_cases=24,
                            verified_cases=24,constructed_only=True))
    inputs=dict(data_access='original-D33-only',d33_completion=str(root/'COMPLETE.json'),
        d33_completion_sha256=archive.digest(root/'COMPLETE.json'),qualification_complete=str(qualification))
    config=dict(owner_reviewed=True,source_kind='authenticated-D33',fixture_only=False,
        source_decisions=stage.DECISIONS,qualification_complete_sha256=archive.digest(qualification))
    return inputs,config,raw,prior


def source_terminal(tmp_path, monkeypatch):
    inputs,config,raw,prior=world(tmp_path,monkeypatch)
    root=tmp_path/'invented-native'; stage.execute(root/'output',inputs,config)
    verified=stage.verify(root/'output',inputs,config)
    write(root/'PLAN.json',dict(module='runners.drive.cards.week6_kp_source_stage_parity_archive_v1',
                              inputs=inputs,config=config))
    for i,name in enumerate(('OWNER','EXECUTE_NATIVE','VERIFY_NATIVE','EXECUTE_CHILD','VERIFY_CHILD')):
        value=dict(native=dict(pid=1000000+i,created_ticks=100+i,executable='constructed-only'))
        if name=='OWNER':value['plan_sha256']=archive.digest(root/'PLAN.json')
        write(root/(name+'.json'),value)
    for op in ('EXECUTE','VERIFY'):
        write(root/(op+'_JOB_USAGE.json'),dict(cpu_seconds=1.,exit_code=0,
            includes_all_descendants_and_exited_processes=True,termination_margin_cpu_seconds=0.))
        write(root/(op+'_ENVIRONMENT.json'),dict(threads=2,pools=[dict(num_threads=2)]))
    write(root/'VERIFIED.json',verified);write(root/'ADMISSION.json',dict(lease=str(tmp_path/'lease.json')))
    def reseal():
        outputs={p.relative_to(root).as_posix():archive.digest(p) for p in root.rglob('*')
                 if p.is_file() and p.name!='COMPLETE.json'}
        write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,cpu_seconds=2.,outputs=outputs))
        return dict(data_access='original-D33-only',source_stage_complete=str(root/'COMPLETE.json'),
            source_stage_complete_sha256=archive.digest(root/'COMPLETE.json'),
            source_stage_seal_sha256=archive.digest(root/'output/SEAL.json'),
            original_source_completion_sha256=inputs['d33_completion_sha256'])
    monkeypatch.setattr(capsule,'native_identity',lambda pid:None)
    return root,reseal,reseal()


def test_whole_original_loader_stage_replay_consumer(tmp_path,monkeypatch):
    root,_,inputs=source_terminal(tmp_path,monkeypatch)
    result=capsule.load_authenticated(inputs,decisions=stage.DECISIONS)
    assert len(result['rows'])==1
    row=result['rows'][0]
    assert (row['writer'],row['session'],row['index'])==('W','S',0)
    assert row['kp1_exclusions']==['sixth_following_word_not_observed']
    assert row['continuation_exclusions']==['three_following_words_not_observed']
    assert row['kp3_exclusions']==['word_not_typed_in_earlier_completed_session']
    assert row['deletion'] is None and row['continuation_surprise'] is None
    assert result['frozen_fit']=={'coefficients':{'intercept':0.},'variance_ratio':0.}
    assert archive.digest(root/'output/CORPUS.json.gz')==archive.digest(root/'output/fresh-source-replay/CORPUS.json.gz')


def test_whole_loader_rejects_other_historical_output_change(tmp_path,monkeypatch):
    inputs,config,_,prior=world(tmp_path,monkeypatch)
    write(prior/'output/SUPPORTED_ROSTER.json',{'changed':True})
    with pytest.raises(ValueError,match='prior completed output changed'): stage.project(inputs,config)


def test_whole_loader_rejects_changed_original_raw_bytes(tmp_path,monkeypatch):
    inputs,config,raw,_=world(tmp_path,monkeypatch)
    raw.write_bytes(raw.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='Source changed after authentication'): stage.project(inputs,config)


def test_consumer_refuses_old_producer_identity(tmp_path,monkeypatch):
    root,reseal,_=source_terminal(tmp_path,monkeypatch)
    plan=archive.read(root/'PLAN.json');plan['module']='runners.drive.cards.week6_kp_source_stage_v1'
    write(root/'PLAN.json',plan)
    owner=archive.read(root/'OWNER.json');owner['plan_sha256']=archive.digest(root/'PLAN.json');write(root/'OWNER.json',owner)
    with pytest.raises(ValueError,match='Wrong complete source module'):
        capsule.load_authenticated(reseal(),decisions=stage.DECISIONS)


def test_consumer_refuses_changed_archived_resolution(tmp_path,monkeypatch):
    root,reseal,_=source_terminal(tmp_path,monkeypatch)
    seal=archive.read(root/'output/SEAL.json');seal['metadata_resolution']['original_sha256']='0'*64
    write(root/'output/SEAL.json',seal)
    with pytest.raises(ValueError,match='archived metadata proof'):
        capsule.load_authenticated(reseal(),decisions=stage.DECISIONS)


def test_consumer_unknown_native_still_propagates(tmp_path,monkeypatch):
    _,_,inputs=source_terminal(tmp_path,monkeypatch)
    def unknown(pid):raise PermissionError(13,'constructed inaccessible native')
    monkeypatch.setattr(capsule,'native_identity',unknown)
    with pytest.raises(PermissionError):capsule.load_authenticated(inputs,decisions=stage.DECISIONS)


def test_rider_body_only_changes_capsule_import():
    old=Path(old_rider.__file__).read_text(encoding='utf8')
    expected=old.replace('from . import week6_kp_capsule_source_v1 as source',
        'from . import week6_kp_capsule_source_parity_archive_v1 as source')
    assert Path(rider.__file__).read_text(encoding='utf8')==expected
