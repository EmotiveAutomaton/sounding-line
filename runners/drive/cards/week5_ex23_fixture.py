"""Constructed EX2/EX3 joins and actual exporter execution/replay boundaries.

The EX2 fixture substitutes only ancestor authentication with a fully sealed
constructed bank. Its saved classifier predictions are constructed, not fitted.
The EX3 fixture substitutes only read-only git HEAD/status metadata. Original
source parsing, sampling, joins, offsets and exporter replay are exercised.
Neither substitute qualifies a human ancestor; production keeps the original
complete publication/source gates and independently qualified parents.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_ex2 as ex2
from . import week5_ex3 as ex3
from . import week5_engine_export_io as common


def seal(root,module,inputs,config):
    common.io.write_json(root/'PLAN.json',dict(module=module,inputs=inputs,config=config))
    common.io.write_json(root/'VERIFIED.json',dict(verified=True,fixture_only=True))
    names=[p for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json']
    common.io.write_json(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():common.io.sha(p) for p in names}))


@contextmanager
def alias(obj,name,value):
    old=getattr(obj,name)
    try:setattr(obj,name,value);yield
    finally:setattr(obj,name,old)


@contextmanager
def yield_after_metadata_block(output):
    target=Path(output).resolve();writer=common.io.write_json
    def write(path,value):
        writer(path,value)
        if (Path(path).resolve()==target/'PROGRESS.json' and value.get('phase')=='EX2_metadata'
            and value.get('completed')==1):
            writer(target/'YIELD_REQUEST.json',dict(constructed_fixture=True,no_scientific_effect=True))
    with alias(common.io,'write_json',write):yield


def ex2_source(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);salt=b'x'*32
    saltpath=root/'salt.bin';saltpath.write_bytes(salt)
    feature_root=root/'feature';analysis_root=root/'analysis';sources=[];blocks=[];all_rows=[]
    for site in ex2.collection.SITES:
        source_root=root/site;records=[]
        for n in range(1000):
            records.append(dict(editor=ex2.source.salted(salt,site+'-user',n%5),
                post=ex2.source.salted(salt,site+'-post',n+1),stamp=f'2020-01-01T00:{n//60:02d}:{n%60:02d}',
                site=site,type=5,reason=ex2.source.PRIMARY[n%5],self_edit=False,owner_known=True,
                before=f'Before fixture {site} {n}',after=f'After fixture {site} {n}'))
        output=source_root/'output';(output/'xml').mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(records),output/'edits.parquet')
        xml=output/'xml/Posts.xml';xml.write_text('<posts>'+''.join(f'<row Id="{n+1}" />' for n in range(1000))+'</posts>',encoding='utf8')
        common.io.write_json(output/'SOURCE.json',dict(member_sha256={'Posts.xml':common.io.sha(xml)}))
        seal(source_root,'constructed.GO3.source',dict(salt=str(saltpath)),{})
        info=dict(site=site,root=str(source_root),projection=str(output/'edits.parquet'),
            rows=len(records),salt_sha256=common.io.sha(saltpath),complete_sha256=common.io.sha(source_root/'COMPLETE.json'))
        sources.append(info)
        for start in range(0,len(records),512):
            metadata=[{k:r[k] for k in ex2.collection.METADATA} for r in records[start:start+512]]
            name=f'blocks/{len(blocks):07d}.parquet';path=feature_root/'output'/name;path.parent.mkdir(parents=True,exist_ok=True)
            pq.write_table(pa.Table.from_pylist(metadata),path)
            blocks.append(dict(site=site,first_row=start,rows=len(metadata),path=name,sha256=common.io.sha(path)))
            all_rows.extend(metadata)
    keys=sorted({r['editor'] for r in all_rows});assignment={w:i%5 for i,w in enumerate(np.random.default_rng(ex2.source.core.SEED).permutation(keys))}
    for fold in range(5):
        indices=np.array([i for i,row in enumerate(all_rows) if assignment[row['editor']]==fold],dtype=np.int64)
        predicted=np.array([ex2.source.PRIMARY.index(all_rows[i]['reason']) for i in indices],dtype=np.int64)
        path=analysis_root/'output/classifier/folds'/f'{fold}.npz';path.parent.mkdir(parents=True,exist_ok=True)
        np.savez(path,indices=indices,prediction=predicted)
    bank=dict(blocks=blocks,binding=dict(provenance=dict(sources=sources)))
    common.io.write_json(feature_root/'output/FEATURES.json',bank)
    seal(feature_root,'constructed.GO3.feature',{},{});seal(analysis_root,'constructed.GO3.analysis',{}, {})
    return dict(analysis_run=str(analysis_root)),feature_root,bank,sources


def ex2_auth(feature_root,bank,sources):
    def authenticate(inputs,stop):
        root,_,_=common.complete(inputs['analysis_run'],'constructed.GO3.analysis')
        common.complete(feature_root,'constructed.GO3.feature')
        for info in sources:common.complete(info['root'],'constructed.GO3.source')
        binding=dict(constructed=True,module_sha256=common.io.sha(ex2.__file__),
            analysis_complete=common.io.sha(root/'COMPLETE.json'),feature_complete=common.io.sha(feature_root/'COMPLETE.json'))
        return root,feature_root,bank,sources,binding
    return authenticate


def ex3_source(root):
    root=Path(root);repo=root/'public';repo.mkdir(parents=True,exist_ok=True);salt=b'y'*32
    saltpath=root/'salt.bin';saltpath.write_bytes(salt);documents=[]
    for n in range(50):
        text=(f'PEP: {n}\nAuthor: Fixture Author {n%5}\nType: Standards Track\n\n'
            'Abstract\n========\nA public proposal.\n\nMotivation\n==========\n'
            f'Goal {n}.\n\nNested\n------\nNested goal evidence.\n\n'
            'Specification\n=============\nMechanism.\n\nCopyright\n=========\nPublic domain.\n')
        path=repo/f'pep-{n:04d}.rst';path.write_text(text,encoding='utf8',newline='\n')
        value,reason=ex3.core.parse_document(text,'peps',salt);assert reason is None
        value.update(document=f'document_{n:05d}',relative_path=path.name,source_sha256=common.io.sha(path),head=ex3.core.PINS['peps'])
        documents.append(value)
    source_root=root/'source';common.io.write_json(source_root/'output/documents.json',{'documents':documents})
    seal(source_root,'runners.drive.cards.week5_go',dict(peps=str(repo),salt=str(saltpath)),{'phase':'prepare'})
    inputs=dict(documents=str(source_root/'output/documents.json'));config={'phase':'GO1-prepare','distractors':49}
    rows,allocation=ex3.pipeline.prepared_rows(inputs,config)
    prepared=root/'prepare';common.io.write_json(prepared/'output/PREPARED.json',dict(source_only=True,
        module_sha256=common.io.sha(ex3.go1.__file__),rows_binding=ex3.digest(rows),allocation_binding=ex3.digest(allocation)))
    seal(prepared,ex3.GO1_MODULE,inputs,config)
    return {'go1_prepare':str(prepared)}


def git_metadata(repo,*args):
    if args==('rev-parse','HEAD'):return ex3.core.PINS['peps']+'\n'
    if args==('status','--porcelain'):return ''
    raise ValueError('Fixture refuses non-metadata git operation')


def execute(output,inputs,config):
    if inputs or set(config)!={'card'} or config['card'] not in ('EX2','EX3'):
        raise ValueError('Only named constructed export qualification is allowed')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config['card']=='EX2':
        args,feature_root,bank,sources=ex2_source(output/'constructed')
        with alias(ex2,'authenticate',ex2_auth(feature_root,bank,sources)):
            with yield_after_metadata_block(output/'consumer'):
                first=ex2.execute(output/'consumer',args,{'max_wall_seconds':120})
            assert first['status']=='yielded' and first['completed']==1
            (output/'consumer/YIELD_REQUEST.json').unlink()
            result=ex2.execute(output/'consumer',args,{'max_wall_seconds':120})
        assert result.get('complete_export') and result['rows']==5000
        expected=dict(rows=5000,all_categories_1000=all(n==1000 for n in result['category_counts'].values()))
    else:
        args=ex3_source(output/'constructed')
        with alias(ex3.core,'git',git_metadata):
            first=ex3.execute(output/'consumer',args,{'max_new_documents':1,'max_wall_seconds':120})
            assert first['status']=='yielded' and first['completed']==1
            result=ex3.execute(output/'consumer',args,{'max_new_documents':50,'max_wall_seconds':120})
        assert result.get('complete_export') and result['queries']==50
        expected=dict(queries=50,all_rosters_49=True,checkpoint_reentry=True)
    record=dict(card=config['card'],constructed=True,no_human_source=True,no_model_fit=True,
        no_materializer_run=True,authentication_substitute_disclosed=True,**expected)
    common.io.write_json(output/'FIXTURE.json',record);return record


def verify(output,inputs,config):
    output=Path(output);card=config['card'];constructed=output/'constructed'
    if card=='EX2':
        feature_root=constructed/'feature';bank=common.read(feature_root/'output/FEATURES.json');sources=bank['binding']['provenance']['sources']
        with alias(ex2,'authenticate',ex2_auth(feature_root,bank,sources)):
            if not (output/'consumer/independent-replay/RESULT.json').exists():
                with yield_after_metadata_block(output/'consumer/independent-replay'):
                    first=ex2.verify(output/'consumer',{'analysis_run':str(constructed/'analysis')},{'max_wall_seconds':120})
                assert first['status']=='yielded' and first['verified'] is False and first['completed']==1
                (output/'consumer/independent-replay/YIELD_REQUEST.json').unlink()
            result=ex2.verify(output/'consumer',{'analysis_run':str(constructed/'analysis')},{'max_wall_seconds':120})
    else:
        args={'go1_prepare':str(constructed/'prepare')}
        with alias(ex3.core,'git',git_metadata):
            if not (output/'consumer/independent-replay/RESULT.json').exists():
                first=ex3.verify(output/'consumer',args,{'max_new_documents':1,'max_wall_seconds':120})
                assert first['status']=='yielded' and first['verified'] is False
            result=ex3.verify(output/'consumer',args,{'max_new_documents':50,'max_wall_seconds':120})
    if result.get('verified') is not True:raise ValueError('Complete constructed export replay required')
    return dict(verified=True,complete_constructed_export_replayed=True,no_materializer_run=True)
