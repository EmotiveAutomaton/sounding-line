"""Raw audit composition fixtures; complete workbook parsing has a separate actual rehearsal."""
import copy

import pytest

from runners.stage9 import closure_raw as subject, argrewrite, common, queue
from runners.stage9.common import closure, digest, file_hash, read, write


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    for module in (subject, common, queue): monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    prepared=tmp_path/'prepared';archive=tmp_path/'archive';raw=tmp_path/'raw/source.txt'
    raw.parent.mkdir();raw.write_text('previously exposed fixture')
    sources={}
    for name in ('runners/stage9/argrewrite.py','runners/stage9/common.py','runners/run_arg_replication.py'):
        path=archive/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('literal original source '+name)
        sources[name]=file_hash(path)
    source={'files':sources,'sha256':digest(sources)};write(archive/'SOURCE.json',source)
    identity={'sources':source,'inputs':closure([raw]),'construction':'literal canonical fixture',
              'exposure':'already exposed fixture','rights_basis':'fixture'}
    essays={'one':{'group':'one','units':[{'usable':False,'exclusion':'multi-purpose unit'}],
                    'draft_checks':{'middle_table_continuity':False},'future_usable':False}}
    ledger=[{'group':'one','attempts':1,'usable':0}]
    summary={'completed':True,'historical_v4_exact':True,'reserve_groups':0,'exclusions':{'multi-purpose unit':1}}
    write(prepared/'IDENTITY.json',identity);write(prepared/'LEDGER.json',ledger)
    write(prepared/'essays/one.json',essays['one'])
    write(prepared/'COMPLETE.json',{'identity_sha256':digest(identity),**summary,'elapsed_seconds':1.,'completed_at':2.})
    def inputs():
        return [raw],[],{**copy.deepcopy(identity),'inputs':closure([raw])}
    monkeypatch.setattr(argrewrite,'raw_inputs',inputs)
    monkeypatch.setattr(argrewrite,'reconstruct',lambda *args:copy.deepcopy((essays,ledger,summary)))
    return prepared,archive,raw,identity


def changed(path, key, value):
    obj=read(path);obj[key]=value;write(path,obj)


def test_read_only_raw_reconstruction_retains_exclusions_without_new_exposure(fixture):
    prepared,archive,raw,identity=fixture;before=closure([prepared,archive,raw])
    result=subject.argrewrite(prepared,archive)
    assert result['status']=='RECONSTRUCTED' and result['essay_groups']==1
    assert result['prepared_identity_sha256']==digest(identity)
    assert result['new_fits']==result['new_reader_calls']==result['new_reserve_openings']==0
    assert not result['scientific_admission'] and closure([prepared,archive,raw])==before


@pytest.mark.parametrize('fault',['raw_changed','archive_changed','archive_map_changed','identity',
    'invented_reserve','failed_canonical','ledger','extra_essay','missing_essay','changed_essay','summary','bad_time'])
def test_raw_audit_refuses_original_input_or_saved_payload_substitution(fixture,fault):
    prepared,archive,raw,identity=fixture
    if fault=='raw_changed':raw.write_text('changed')
    elif fault=='archive_changed':(archive/'runners/stage9/argrewrite.py').write_text('changed')
    elif fault=='archive_map_changed':write(archive/'SOURCE.json',{'files':{}})
    elif fault=='identity':changed(prepared/'COMPLETE.json','identity_sha256','wrong')
    elif fault=='invented_reserve':changed(prepared/'COMPLETE.json','reserve_groups',1)
    elif fault=='failed_canonical':changed(prepared/'COMPLETE.json','historical_v4_exact',False)
    elif fault=='ledger':write(prepared/'LEDGER.json',[])
    elif fault=='extra_essay':write(prepared/'essays/extra.json',{})
    elif fault=='missing_essay':(prepared/'essays/one.json').unlink()
    elif fault=='changed_essay':changed(prepared/'essays/one.json','future_usable',True)
    elif fault=='summary':changed(prepared/'COMPLETE.json','exclusions',{})
    else:changed(prepared/'COMPLETE.json','elapsed_seconds',-1)
    with pytest.raises(ValueError):subject.argrewrite(prepared,archive)


def setup_queue(fixture,monkeypatch):
    prepared,archive,raw,identity=fixture;repo=prepared.parent;work=repo/'work';q=repo/'queue'
    job={'id':'cases','module':'runners.stage9.revision_cases','produces':'work/COMPLETE.json'}
    plan={'raw_source_reviews':{'cases':{'kind':'argrewrite','prepared':'prepared','source_archive':'archive'}}}
    write(work/'IDENTITY.json',{'prepared_identity_sha256':digest(identity)})
    write(q/'STATUS.json',{'jobs':{'cases':{'status':'COMPLETE'}}})
    monkeypatch.setattr(subject,'verify_committed',lambda *args:None)
    return plan,q,{'cases':job}


def test_original_manual_review_binds_the_actual_preparation_input(fixture,monkeypatch):
    plan,q,prior=setup_queue(fixture,monkeypatch)
    assert subject.queue_audits(plan,q,prior)['jobs']['cases']['status']=='RECONSTRUCTED'
    assert subject.queue_audits({},q,prior)['jobs']=={}
    changed(fixture[0].parent/'work/IDENTITY.json','prepared_identity_sha256','unrelated')
    with pytest.raises(ValueError):subject.queue_audits(plan,q,prior)


@pytest.mark.parametrize('fault',['unknown_job','parser','producer','running'])
def test_raw_review_cannot_invent_source_coverage(fixture,monkeypatch,fault):
    plan,q,prior=setup_queue(fixture,monkeypatch)
    if fault=='unknown_job':plan['raw_source_reviews']['unknown']=plan['raw_source_reviews'].pop('cases')
    elif fault=='parser':plan['raw_source_reviews']['cases']['kind']='unknown'
    elif fault=='producer':prior['cases']['module']='runners.stage9.queue_branch_fixture'
    else:write(q/'STATUS.json',{'jobs':{'cases':{'status':'RUNNING'}}})
    with pytest.raises(ValueError):subject.queue_audits(plan,q,prior)


def test_failed_preparation_retains_reason_without_parsing_raw_data(fixture,monkeypatch):
    plan,q,prior=setup_queue(fixture,monkeypatch)
    original={'status':'FAILED','reason':'original refused preparation','disposition_sha256':'a'*64}
    write(q/'STATUS.json',{'jobs':{'cases':original}})
    monkeypatch.setattr(subject,'argrewrite',lambda *args:pytest.fail('failed source was parsed'))
    assert subject.queue_audits(plan,q,prior)['jobs']['cases']==original


def scientific_roster():
    modules = {'argrewrite': 'revision_cases', 'iterater': 'iterater_cases',
               'commitbench': 'commit_jobs', 'broll': 'broll_jobs',
               'coauthor': 'record_jobs', 'scholawrite': 'record_jobs'}
    jobs = {}
    for kind, module in modules.items():
        args = [] if module.endswith('_cases') else ['prepare']
        if module == 'record_jobs':
            args += ['--dataset', kind]
        jobs[kind] = {'id': kind, 'module': 'runners.stage9.' + module, 'arguments': args}
    # A second rotation of the same corpus still requires its own reviewed producer.
    jobs['scholawrite-fold-2'] = copy.deepcopy(jobs['scholawrite'])
    jobs['scholawrite-fold-2'].update(id='scholawrite-fold-2')
    jobs['scholawrite-fold-2']['arguments'] += ['--fold', '2']
    reviews = {key: {'kind': 'scholawrite' if key.startswith('scholawrite') else key,
                     'prepared': 'prepared/' + key, 'source_archive': 'archive/' + key}
               for key in jobs}
    # Fitting and prediction dispatches must not be mistaken for raw preparation.
    jobs['prediction'] = {'id': 'prediction', 'module': 'runners.stage9.record_jobs',
                          'arguments': ['execute', '--dataset', 'coauthor']}
    return {'kind': 'science', 'jobs': list(jobs.values()), 'raw_source_reviews': reviews}, jobs


def test_complete_scientific_roster_is_read_only_and_retains_every_failed_source(tmp_path, monkeypatch):
    plan, jobs = scientific_roster()
    subject.validate_scientific_reviews(plan, jobs)
    before = copy.deepcopy(plan)
    states = {key: {'status': 'FAILED' if i % 2 else 'NOT_RUN',
                    'reason': 'original source unavailable', 'disposition_sha256': str(i) * 64}
              for i, key in enumerate(jobs)}
    write(tmp_path/'STATUS.json', {'jobs': states})
    for kind in ('argrewrite', 'coauthor', 'scholawrite'):
        monkeypatch.setattr(subject, kind, lambda *args: pytest.fail('failed source parsed'))
    results = subject.queue_audits(plan, tmp_path, jobs)
    assert set(results['jobs']) == set(plan['raw_source_reviews'])
    assert all(results['jobs'][key] == states[key] for key in results['jobs'])
    assert plan == before and results['scientific_admission'] is False


@pytest.mark.parametrize('missing', ['argrewrite', 'iterater', 'commitbench', 'broll',
                                    'coauthor', 'scholawrite', 'scholawrite-fold-2'])
def test_each_scientific_preparation_requires_its_review_before_any_queue_read(tmp_path, missing):
    plan, jobs = scientific_roster()
    del plan['raw_source_reviews'][missing]
    # There is deliberately no queue or raw input: omission must refuse first.
    with pytest.raises(ValueError, match='cover every human preparation exactly'):
        subject.queue_audits(plan, tmp_path/'absent', jobs)


@pytest.mark.parametrize('fault', ['extra', 'wrong_parser', 'wrong_record_dataset',
                                 'duplicate_dataset', 'missing_dataset_value', 'empty_archive'])
def test_scientific_roster_refuses_substituted_or_ambiguous_routes(fault):
    plan, jobs = scientific_roster()
    if fault == 'extra':
        plan['raw_source_reviews']['prediction'] = copy.deepcopy(plan['raw_source_reviews']['coauthor'])
    elif fault == 'wrong_parser':
        plan['raw_source_reviews']['iterater']['kind'] = 'argrewrite'
    elif fault == 'wrong_record_dataset':
        plan['raw_source_reviews']['coauthor']['kind'] = 'scholawrite'
    elif fault == 'duplicate_dataset':
        jobs['coauthor']['arguments'] += ['--dataset', 'scholawrite']
    elif fault == 'missing_dataset_value':
        jobs['coauthor']['arguments'] = ['prepare', '--dataset']
    else:
        plan['raw_source_reviews']['coauthor']['source_archive'] = ' '
    with pytest.raises(ValueError):
        subject.validate_scientific_reviews(plan, jobs)


def test_launch_checks_raw_coverage_before_accepting_other_evidence(monkeypatch):
    from runners.stage9 import launch
    plan, jobs = scientific_roster()
    del plan['raw_source_reviews']['coauthor']
    plan['sources'] = {}
    monkeypatch.setattr(queue, 'validate_manifest', lambda p: True)
    monkeypatch.setattr(queue, 'verify_sources', lambda s: None)
    monkeypatch.setattr(launch, 'checked', lambda *args: pytest.fail('accepted other launch evidence'))
    with pytest.raises(ValueError, match='cover every human preparation exactly'):
        launch.validate(plan, {})


def test_historical_component_scope_does_not_claim_complete_scientific_roster():
    plan, jobs = scientific_roster()
    plan['kind'] = 'prelaunch_rehearsal'
    plan['raw_source_reviews'] = {}
    subject.validate_scientific_reviews(plan, jobs)
