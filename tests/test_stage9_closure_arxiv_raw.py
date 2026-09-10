"""Original annotations and rights exclusions reconstruct; invalid archives refuse."""
from copy import deepcopy
import pytest
from runners.stage9 import arxivedits,closure_arxiv_raw as subject,closure_raw,common,queue
from runners.stage9.common import closure,digest,file_hash,read,write


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    for module in (subject,closure_raw,common,queue):monkeypatch.setattr(module,'REPO',tmp_path)
    monkeypatch.setattr(queue,'ROOT',tmp_path)
    prepared=tmp_path/'prepared';archive=tmp_path/'archive';raw=tmp_path/'raw.json';write(raw,{'original':'source'})
    files={}
    for name in ('arxivedits','common'):
        path=archive/'runners/stage9'/(name+'.py');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('original '+name);files['runners/stage9/'+name+'.py']=file_hash(path)
    source={'files':files,'sha256':digest(files)};write(archive/'SOURCE.json',source)
    identity={'release_pin':'literal-original-pin','input_files':{'raw':file_hash(raw)},'sources':source,
        'rights_selection':['original-license'],'split':'development-only','canonical_rule':'combination zero'}
    pairs={'pair':{'source_pair':{'canonical':'old to new','alternative':'kept privately'},
        'correspondence':{'licenses':['original-license'],'exclusion':None}}}
    attempts=[{'key':'pair','exclusion':None},{'key':'excluded','exclusion':'unsupported-rights'}]
    records=[{'key':'edit','pair':'pair','before':'old','artifact':'new','label':'Content','independent_unit':'arxiv:p'}]
    lineages={'arxiv:p':{'pairs':['pair']}}
    summary={'source_counts_match':True,'versions':2,'attempted_pairs':2,'selected_pairs':1,
        'paper_lineages':1,'usable_edits':1,'reserve_groups':0,'pair_exclusions':{'unsupported-rights':1},
        'limits':['annotated span agreement only']}
    write(prepared/'IDENTITY.json',identity);write(prepared/'pairs/pair.json',pairs['pair'])
    for name,value in [('ATTEMPTS.json',attempts),('RECORDS.json',records),('LINEAGES.json',lineages)]:write(prepared/name,value)
    done={'identity_sha256':digest(identity),**summary,'elapsed_seconds':1.,'completed_at':2.,
        'output_hashes':{n:file_hash(prepared/n) for n in ('ATTEMPTS.json','RECORDS.json','LINEAGES.json')}}
    write(prepared/'COMPLETE.json',done)
    monkeypatch.setattr(arxivedits,'raw_inputs',lambda:({'raw':raw},{**deepcopy(identity),'input_files':{'raw':file_hash(raw)}}))
    monkeypatch.setattr(arxivedits,'reconstruct',lambda *args:deepcopy((pairs,attempts,records,lineages,summary)))
    return prepared,archive,raw


def review(fixture):
    prepared,archive,_=fixture
    return {'kind':'arxivedits','prepared':str(prepared),'source_archive':str(archive),
        'identity_sha256':digest(read(prepared/'IDENTITY.json')),'complete_sha256':file_hash(prepared/'COMPLETE.json')}


def test_whole_preparation_reconstructs_without_changing_bytes(fixture):
    prepared,archive,raw=fixture;before=closure([prepared,archive,raw]);result=subject.inspect(prepared,archive)
    assert (result['attempted_pairs'],result['selected_pairs'],result['paper_lineages'],result['usable_edits'])==(2,1,1,1)
    assert result['new_fits']==result['new_reader_calls']==result['new_reserve_openings']==result['reserve_groups']==0
    assert not result['scientific_admission'] and closure([prepared,archive,raw])==before


@pytest.mark.parametrize('fault',['raw','archive_bytes','archive_map','identity','rights','reserve','counts',
    'pair','alternative','extra_pair','missing_pair','span','excluded','group','hash','time'])
def test_altered_original_evidence_and_rehashed_semantics_refuse(fixture,fault):
    prepared,archive,raw=fixture;done=read(prepared/'COMPLETE.json')
    if fault=='raw':write(raw,{'changed':True})
    elif fault=='archive_bytes':(archive/'runners/stage9/arxivedits.py').write_text('changed')
    elif fault=='archive_map':
        src=read(archive/'SOURCE.json');src['files']['runners/stage9/arxivedits.py']='0'*64;src['sha256']=digest(src['files']);write(archive/'SOURCE.json',src)
    elif fault=='identity':done['identity_sha256']='changed'
    elif fault=='rights':
        identity=read(prepared/'IDENTITY.json');identity['rights_selection']=['invented'];write(prepared/'IDENTITY.json',identity);done['identity_sha256']=digest(identity)
    elif fault=='reserve':done['reserve_groups']=1
    elif fault=='counts':done['source_counts_match']=False
    elif fault in ('pair','alternative'):
        path=prepared/'pairs/pair.json';value=read(path)
        if fault=='pair':value['correspondence']['licenses']=['invented']
        else:value['source_pair']['alternative']='discarded'
        write(path,value)
    elif fault=='extra_pair':write(prepared/'pairs/extra.json',{})
    elif fault=='missing_pair':(prepared/'pairs/pair.json').unlink()
    elif fault=='span':
        path=prepared/'RECORDS.json';rows=read(path);rows[0]['artifact']='wrong';write(path,rows)
    elif fault=='excluded':write(prepared/'ATTEMPTS.json',[])
    elif fault=='group':write(prepared/'LINEAGES.json',{'different':{'pairs':['pair']}})
    elif fault=='hash':done['output_hashes']['RECORDS.json']='changed'
    else:done['elapsed_seconds']=-1.
    if fault in ('span','excluded','group'):
        done['output_hashes']={n:file_hash(prepared/n) for n in done['output_hashes']}
    write(prepared/'COMPLETE.json',done)
    with pytest.raises((ValueError,FileNotFoundError)):subject.inspect(prepared,archive)


@pytest.mark.parametrize('fault',[None,'duplicate','kind','identity','complete','extra'])
def test_explicit_archival_review_has_original_bindings(fixture,fault):
    item=review(fixture);items=[item]
    if fault=='duplicate':items.append(deepcopy(item))
    elif fault=='kind':item['kind']='unsupported'
    elif fault=='identity':item['identity_sha256']='changed'
    elif fault=='complete':item['complete_sha256']='changed'
    elif fault=='extra':item['invented_producer']='ran'
    if fault:
        with pytest.raises(ValueError):subject.archive_audits(items)
    else:
        result=subject.archive_audits(items)
        assert set(result['preparations'])=={'prepared'} and not result['new_queue_producer_execution_inferred']


def test_archival_queue_composition_keeps_active_and_historical_sources_distinct(fixture):
    prepared,_,_=fixture;queue_path=prepared.parent/'queue';write(queue_path/'STATUS.json',{'jobs':{}})
    bare=closure_raw.queue_audits({},queue_path,{})
    assert 'historical_preparations' not in bare
    result=closure_raw.queue_audits({'raw_preparation_archives':[review(fixture)]},queue_path,{})
    assert result['jobs']=={} and not result['scientific_admission']
    assert result['historical_preparations']==subject.archive_audits([review(fixture)])


def test_shared_reconstruction_has_independent_release_counts_and_rights_answers(monkeypatch):
    objects={};remaining_extra_versions=288;allowed='http://creativecommons.org/licenses/by/4.0/'
    for lane,n_pairs,n_papers,n_edits in [('train',600,526,1254),('dev',200,75,438),('test',200,150,430)]:
        papers={}
        for i in range(n_papers):
            versions=3 if remaining_extra_versions else 2;remaining_extra_versions-=versions==3
            license=allowed if i==0 else 'unsupported'
            papers[lane+str(i)]={'license':{str(v):license for v in range(1,versions+1)},
                **{str(v):{'sentence':'The old.' if v==1 else 'The new.'} for v in range(1,versions+1)}}
        pairs={}
        for i in range(n_pairs):
            count=2+(i<n_edits-2*n_pairs)
            pairs[str(i)]={'arxiv-id':lane+str(i%n_papers),'sentence-1':'The old .','sentence-2':'The new .',
                'sentence-1-level':1,'sentence-2-level':2,
                'edits-combination-0':{str(k):{'type':'Substitute','intention':'Content',
                    'sentence-1-token-indices':[1,2],'sentence-2-token-indices':[1,2]} for k in range(count)},
                'edits-combination-1':{'unchosen':None},'edits-combination-2':{}}
        objects['data/edits/'+lane+'.json']=pairs;objects['data/sentence_alignment/'+lane+'.json']=papers
    monkeypatch.setattr(arxivedits,'read',lambda path:deepcopy(objects[path]))
    pairs,attempts,records,lineages,summary=arxivedits.reconstruct({k:k for k in objects},'literal-pin')
    assert len(attempts)==1000 and len(pairs)==7 and len(records)==17 and len(lineages)==3
    assert summary['versions']==1790 and summary['pair_exclusions']=={'outside_explicit_license_selection':993}
    assert {row['before'] for row in records}=={'old'} and {row['artifact'] for row in records}=={'new'}
    assert all(row['split']=='development' for row in records)
    objects['data/edits/train.json']['0']['edits-combination-0']['0']['sentence-2-token-indices']=[1,99]
    with pytest.raises(ValueError,match='span outside'):arxivedits.reconstruct({k:k for k in objects},'literal-pin')
