"""Exact certified-fit-1 engine departure export; no recipient modifications.

The pinned original modules run unchanged. Product marks are span membership
in summarize_deviation's selected attention list, not a renamed token score.
"""
from pathlib import Path
import importlib,json,os,sys
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from runners.stage9.coauthor import units,text_of,apply_delta

COMMIT='5f3ad0a304727fff5e1a6beca592e786ee71b181'


def modules(source):
    root=Path(source).resolve();manifest=read(root/'MANIFEST.json')
    if manifest['commit']!=COMMIT:raise ValueError('Wrong certified engine commit')
    for name,sha in manifest['files'].items():
        p=(root/name).resolve();p.relative_to(root)
        if filehash(p)!=sha:raise ValueError('Pinned engine source changed')
    sys.path.insert(0,str(root))
    surface=importlib.import_module('tompathy_engine.preview.surface')
    readers=importlib.import_module('tompathy_engine.preview.readers')
    for module in (surface,readers):
        if not Path(module.__file__).resolve().is_relative_to(root):raise ValueError('Another engine import shadowed frozen source')
    return surface,readers


def prepare(output,inputs,config,verifying=False):
    if set(inputs)!={'at_source_root','raw_roster','repo_root'}:raise ValueError('Exact final-document source required')
    source=authenticate(inputs['at_source_root'])/'output';raw={r['session']:r for r in read(inputs['raw_roster'])}
    root=Path(output);root.mkdir(parents=True,exist_ok=True);index=[]
    for n,entry in enumerate(read(source/'INDEX.json')):
        path=source/entry['file']
        if filehash(path)!=entry['sha256']:raise ValueError('AT source changed')
        allrows=gzread(path)['rows'];rows=[r for r in allrows if r['final_supported']]
        if not allrows:continue
        meta=raw[allrows[0]['session']];rawpath=(Path(inputs['repo_root'])/meta['path']).resolve()
        rawpath.relative_to(Path(inputs['repo_root']).resolve())
        if filehash(rawpath)!=meta['source_sha256']:raise ValueError('Raw final document changed')
        events=[json.loads(line) for line in rawpath.read_text(encoding='utf8').splitlines() if line]
        doc=units(events[0]['currentDoc']);owners=['prompt']*len(doc)
        for event in events:doc,owners,_=apply_delta(doc,owners,event.get('textDelta'))
        text=text_of(doc);mapped=[]
        for row in rows:
            start=len(row['final_prefix']);end=start+len(row['target'])
            if text[start:end]!=row['target']:raise ValueError('Final occurrence source span differs')
            mapped.append(dict(row_key=row['row_key'],start=start,end=end))
        value=dict(document=text,words=mapped);name=f'documents/document-{n:04d}.json.gz'
        if verifying:
            if gzread(root/name)!=value:raise ValueError('Final document replay differs')
        else:gzip_equal(root/name,value)
        index.append(dict(file=name,sha256=filehash(root/name),words=len(mapped)))
        progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'source',documents=n+1))
    if verifying:
        if read(root/'INDEX.json')!=index:raise ValueError('Engine source roster differs')
        return dict(verified=True,complete_document_replay=True)
    write_equal(root/'INDEX.json',index);return dict(status='complete',scientific_admission=False)


def reader_directory(manifest,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);files={}
    for name,sha in manifest['files'].items():
        source=Path(name)
        if filehash(source)!=sha:raise ValueError('Engine reader source changed')
        target=root/source.name
        if not target.exists():os.link(source,target)
        if filehash(target)!=sha:raise ValueError('Engine reader hardlink changed')
        files[target.name]=sha
    write_equal(root/'manifest.json',dict(model=manifest['model'],revision=manifest['revision'],files=files))
    return root


def map_marks(text,words,result):
    out=[];scorable={(w['start'],w['end']) for row in result['rows'] for w in row['words'] if w['content'] and not w['held']}
    for word in words:
        key=(word['start'],word['end']);a=len(text[:key[0]].encode('utf-16-le'))//2;b=len(text[:key[1]].encode('utf-16-le'))//2
        hits=[r for r in result['attention'] if r['start']<=a and r['end']>=b]
        out.append(dict(row_key=word['row_key'],supported=key in scorable,marked=bool(hits),
                        mark_departure=max((r['departure'] for r in hits),default=0.)))
    return out


def score(output,inputs,config,verifying=False):
    if set(inputs)!={'document','engine_source','model_manifest'}:raise ValueError('Exact certified reader inputs required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);surface,readers=modules(inputs['engine_source'])
    manifest=read(inputs['model_manifest'])
    if manifest['model'] not in ('Qwen/Qwen2.5-0.5B','HuggingFaceTB/SmolLM2-360M'):raise ValueError('Unknown engine reader')
    # Weights remain in ignored storage; the reader's exact file-manifest
    # contract is satisfied without copying model bytes or changing snapshots.
    directory=reader_directory(manifest,root.parent/'reader-files')
    reader=readers.LocalReader(directory,cache=None,device='cpu',threads=2,precision='int8')
    data=gzread(inputs['document']);capture=dict(regions=[dict(id='document',anchor=dict(exact=data['document']))])
    result=surface.deviation_map(capture,reader);mapped=map_marks(data['document'],data['words'],result)
    value=dict(engine_commit=COMMIT,reader=reader.identity,rows=mapped,
               supported=sum(r['supported'] for r in mapped),unsupported=sum(not r['supported'] for r in mapped),
               mark_rule='Exact product attention span contains full word; max exact span departure, zero if unmarked')
    if verifying:
        old=read(root/'SCORES.json')
        if old!=value:raise ValueError('Certified product marks full replay differs')
        return dict(verified=True,complete_exact_reader_replay=True)
    write_equal(root/'SCORES.json',value);return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return (prepare if config.get('operation')=='prepare' else score)(output,inputs,config)
def verify(output,inputs,config):return (prepare if config.get('operation')=='prepare' else score)(output,inputs,config,True)
