"""Used raw rows reconstruct while sealed rows stay outside JSON parsing."""
import json
from pathlib import Path

import pytest

from runners.stage9 import closure_iterater_raw as subject, common, queue, data
from runners.stage9.common import closure, digest, file_hash, read, write
from runners.stage9.reconcile_groups import reconcile


def raw_row(doc, depth, before, after, domain='wiki'):
    return {'doc_id': doc, 'revision_depth': depth, 'domain': domain,
        'before_revision': before, 'after_revision': after, 'sents_char_pos': [],
        'edit_actions': [{'major_intent': 'clarity', 'raw_intents': ['clarity', 'others'], 'type': 'R'}]}


def resign(fixture):
    prepared, archive, case, root = fixture
    metadata = read(case / 'METADATA.json')
    metadata['prepared_files'] = {p: file_hash(p) for p in metadata['prepared_files']}
    write(case / 'METADATA.json', metadata)
    identity = read(case / 'IDENTITY.json'); identity['metadata_sha256'] = digest(metadata)
    write(case / 'IDENTITY.json', identity)
    write(case / 'COMPLETE.json', {'identity_sha256': digest(identity), 'execution_complete': True,
        'outputs': closure([case / n for n in ('IDENTITY.json', 'METADATA.json', 'CASES.json')])})


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / 'results'
    for module in (subject, common, queue):
        monkeypatch.setattr(module, 'REPO', tmp_path)
        monkeypatch.setattr(module, 'ROOT', root)
    prepared = root / 'private/prepared/iterater-v2'; parent = prepared.parent / 'iterater'
    archive = root / 'private/source-archive/original'; case = root / 'private/cases'
    materialized = root / 'private/intake/materialized' / ('a' * 64) / 'IteraTeR'
    selected = {('train', 1): raw_row('d', 0, 'A', 'B'),
                ('train', 2): raw_row('d', 1, 'B', 'C'),
                ('dev', 1): raw_row('d', 2, 'C', 'D', 'unknown'),
                ('test', 1): raw_row('e', 0, 'other', 'revision')}
    source, material = {}, {}
    for split, count in [('train',481),('dev',27),('test',51)]:
        for folder, prefix in [('human_doc_level',''),('human_sent_level','sentence/')]:
            path = materialized / folder / (split+'.json'); path.parent.mkdir(parents=True,exist_ok=True)
            lines = [(json.dumps(selected[(split,n)],ensure_ascii=False) if folder=='human_doc_level' and (split,n) in selected
                      else '{"sealed":true}') for n in range(1,(count if not prefix else 2)+1)]
            path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
            source[prefix+split+'.json'] = file_hash(path)
            material['IteraTeR/'+folder+'/'+split+'.json'] = {'sha256':file_hash(path)}
    write(root/'intake/ITERATER_ARCHIVE.json',{'sha256':'a'*64})
    write(root/'intake/ITERATER_MATERIALIZATION.json',{'archive':'a'*64,'executed':False,'materialized':material})
    files = {}
    for name in ('data.py','reconcile_groups.py'):
        path = tmp_path/'runners/stage9'/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('original '+name)
        target = archive/'runners/stage9'/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(path.read_bytes())
        files['runners/stage9/'+name] = file_hash(path)
    write(archive/'SOURCE.json',{'files':files,'sha256':digest(files)})
    old = {'allocation':{'wiki:d':'train','unknown:d':'reserve','wiki:e':'development','wiki:sealed':'reserve'},
        'duplicates':[],'source':source,'preparation_sha256':files['runners/stage9/data.py'],
        'seed':90619,'initial_schema_exposure':[],'sealed_reserve_fraction':.30,'view_contract':'literal fixture'}
    write(parent/'IDENTITY.json',old)
    # Production reconciliation consumes the canonical saved identity, including
    # its key order, rather than the pre-serialization fixture dictionary.
    old=read(parent/'IDENTITY.json')
    for lane in subject.LANES: write(parent/lane/'records.json',{'opaque_parent_lane':lane})
    audit_path = prepared.parent/'iterater-duplicate-audit-v1.json'
    audit = {'edges':[{'groups':['wiki:d','unknown:d']}],
        'input_files':{str(parent/lane/'records.json'):file_hash(parent/lane/'records.json') for lane in subject.LANES}}
    write(audit_path,audit)
    mapping,allocation,components = reconcile(old['allocation'],audit['edges'])
    identity = {**old,'allocation':allocation,'source_group_repair':{'parent_identity_sha256':digest(old),
        'duplicate_audit_sha256':file_hash(audit_path),'source_sha256':files['runners/stage9/reconcile_groups.py'],
        'old_to_new':mapping,'components':components,
        'rule':'exposed split takes precedence; reserve requires an existing unexposed reserved member; no fresh reserve replacements'}}
    write(prepared/'IDENTITY.json',identity)
    canonical = {}
    for key,row in selected.items():
        item=data.document_record(row,*key,source[key[0]+'.json']); previous=item['group']; unit=mapping[previous]
        canonical[key]={**item,'previous_independent_unit':previous,'previous_split':old['allocation'][previous],
            'independent_unit':unit,'split':allocation[unit]}
    write(prepared/'train/records.json',[canonical[('train',1)],canonical[('train',2)],canonical[('dev',1)]])
    write(prepared/'development/records.json',[canonical[('test',1)]])
    # Literal independently specified successor answers include the repaired alias.
    write(prepared/'train/future_links.json',[
        {'current':canonical[('train',1)]['key'],'future':canonical[('train',2)]['key'],'split':'train'},
        {'current':canonical[('train',2)]['key'],'future':canonical[('dev',1)]['key'],'split':'train'}])
    write(prepared/'development/future_links.json',[])
    write(prepared/'reserve/records.json',{'sealed_labels':'never parse'})
    write(prepared/'reserve/future_links.json',{'sealed_links':'never parse'})
    write(root/'intake/ITERATER_GROUP_REPAIR.json',{'identity_sha256':digest(identity),
        'group_counts':{'train':1,'development':1,'reserve':1},'wholly_new_reserve_groups':0,
        'record_counts':{'train':3,'development':1,'reserve':555}})
    metadata={'prepared_identity_sha256':digest(identity),'prepared_files':{
        str(prepared/lane/name):file_hash(prepared/lane/name) for lane in ('train','development')
        for name in ('records.json','future_links.json')}}
    write(case/'METADATA.json',metadata)
    write(case/'IDENTITY.json',{'operation':'iterater-actual-revision-cases-v1','scope':'pilot','metadata_sha256':digest(metadata)})
    write(case/'CASES.json',{'fixture':'projection validation belongs to closure_cases'})
    value=(prepared,archive,case,root); resign(value)
    return value


def test_all_consumed_rows_votes_repaired_links_and_opaque_reserve(fixture,monkeypatch):
    prepared,archive,case,root=fixture; before=closure([root]); parsed=[]; original_loads=subject.json.loads
    def guarded(value,*args,**kwargs):
        row=original_loads(value,*args,**kwargs)
        if isinstance(value,bytes):
            assert 'sealed' not in row
            parsed.append(row['doc_id'])
        return row
    monkeypatch.setattr(subject.json,'loads',guarded)
    original_read=subject.read
    def no_reserve(path):
        assert not (Path(path).parent.name=='reserve' and Path(path).name in ('records.json','future_links.json'))
        return original_read(path)
    monkeypatch.setattr(subject,'read',no_reserve)
    result=subject.inspect(prepared,archive,case)
    assert parsed==['d','d','d','e'] and result['records']=={'train':3,'development':1}
    assert result['raw_document_rows_parsed']==4 and result['unselected_raw_rows_json_parsed']==0
    assert not result['reserve_payloads_parsed'] and result['new_fits']==result['new_reader_calls']==result['new_reserve_openings']==0
    assert not result['scientific_admission'] and closure([root])==before


@pytest.mark.parametrize('fault',['raw','parser','repair_source','archive_map','repair_mapping','producer',
    'role','offset','vote','missing_row','row_order','link','expanded_lane'])
def test_rehashed_wrong_source_derivation_or_lane_refuses(fixture,fault):
    prepared,archive,case,root=fixture
    if fault=='raw':
        path=root/'private/intake/materialized'/('a'*64)/'IteraTeR/human_doc_level/train.json'; path.write_bytes(path.read_bytes()+b'\n')
    elif fault=='parser':(archive/'runners/stage9/data.py').write_text('different parser')
    elif fault=='repair_source':(subject.REPO/'runners/stage9/reconcile_groups.py').write_text('different repair')
    elif fault=='archive_map':
        source=read(archive/'SOURCE.json'); source['files']['runners/stage9/data.py']='0'*64
        source['sha256']=digest(source['files']);write(archive/'SOURCE.json',source)
    elif fault=='repair_mapping':
        identity=read(prepared/'IDENTITY.json');identity['source_group_repair']['old_to_new']['unknown:d']='wiki:sealed';write(prepared/'IDENTITY.json',identity)
    elif fault in ('producer','role'):
        identity=read(case/'IDENTITY.json');identity['operation' if fault=='producer' else 'scope']='different';write(case/'IDENTITY.json',identity)
    elif fault=='link':write(prepared/'train/future_links.json',[])
    elif fault=='expanded_lane':
        metadata=read(case/'METADATA.json');metadata['prepared_files'][str(prepared/'reserve/records.json')]=file_hash(prepared/'reserve/records.json');write(case/'METADATA.json',metadata)
    else:
        path=prepared/'train/records.json';rows=read(path)
        if fault=='offset':rows[0]['source_line']=3
        elif fault=='vote':rows[0]['raw_votes']=[['clarity']]
        elif fault=='missing_row':rows.pop()
        else:rows.reverse()
        write(path,rows)
    resign(fixture)
    with pytest.raises((ValueError,KeyError)):
        subject.inspect(prepared,archive,case)


def test_shared_document_decoder_keeps_missing_domain_multivotes_and_source_offset():
    row=raw_row('2401.12345v2',4,'a😀','b😀');del row['domain']
    result=data.document_record(row,'test',17,'literal-sha')
    assert result['group']=='unknown:2401.12345v2' and result['source_line']==17
    assert result['labels']==['clarity'] and result['raw_votes']==[['clarity','others']]
    assert result['before']=='a😀' and result['artifact']=='b😀'
    row['edit_actions'][0]['major_intent']='not-in-support'
    with pytest.raises(ValueError):data.document_record(row,'test',17,'literal-sha')


def test_missing_selected_physical_offset_refuses(fixture):
    prepared,_,_,_=fixture; source=read(prepared/'IDENTITY.json')['source']; paths=subject.raw_inputs(source)
    with pytest.raises(ValueError,match='missing'):
        subject.selected_documents(paths,source,{'train':{482},'dev':set(),'test':set()})


@pytest.mark.parametrize('state',['COMPLETE','FAILED','NOT_RUN'])
def test_queue_route_binds_the_actual_human_producer_and_retains_nonexecution(fixture,monkeypatch,state):
    from runners.stage9 import closure_raw
    prepared,archive,case,root=fixture
    monkeypatch.setattr(closure_raw,'REPO',subject.REPO)
    monkeypatch.setattr(closure_raw,'verify_committed',lambda *args:None)
    queue_path=root/'private/queue';record={'status':state}
    if state!='COMPLETE':record.update(reason='original refusal',disposition_sha256='literal')
    write(queue_path/'STATUS.json',{'jobs':{'cases':record}})
    job={'module':'runners.stage9.iterater_cases','produces':str(case/'COMPLETE.json')}
    plan={'raw_source_reviews':{'cases':{'kind':'iterater','prepared':str(prepared),'source_archive':str(archive)}}}
    if state!='COMPLETE':monkeypatch.setattr(subject,'inspect',lambda *args:pytest.fail('nonexecuted source opened'))
    result=closure_raw.queue_audits(plan,queue_path,{'cases':job})['jobs']['cases']
    assert result==record if state!='COMPLETE' else result['case_identity_sha256']==digest(read(case/'IDENTITY.json'))
