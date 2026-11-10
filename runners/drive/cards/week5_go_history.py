"""Pinned local GO2 history and before/after goal-revision comparison.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Future/final text is not a baseline.
Every eligible anchor compares added text before and after its own changed goal.
Identical old/new goals yield exactly zero. Missing history is a source hold,
not a zero. Author resampling retains all their changing-goal anchors.
"""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from . import week5_go as core


def tokens(text):return re.findall(r'\w+',text.casefold(),re.UNICODE)


def token_change(old,new):
    a=tokens(old);b=tokens(new);ops=difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes()
    changed=sum((i2-i1)+(j2-j1) for tag,i1,i2,j1,j2 in ops if tag!='equal')
    added=' '.join(word for tag,i1,i2,j1,j2 in ops if tag!='equal' for word in b[j1:j2])
    return changed/max(1,len(a),len(b)),added


def history_manifest(repo,path):
    """Follow renamed paths backward without fetching any missing Git object."""
    output=core.git(repo,'log','--follow','--format=COMMIT %H %ct','--name-status',core.PINS[repo.name.removeprefix('history-')],'--',path)
    records=[];current=path;entry=None
    for line in output.splitlines():
        if line.startswith('COMMIT '):
            if entry:records.append(entry)
            _,commit,stamp=line.split();entry={'commit':commit,'timestamp':int(stamp),'path':current}
        elif entry and line.startswith('R'):
            bits=line.split('\t')
            if len(bits)==3 and bits[2]==current:entry['path']=bits[2];current=bits[1]
    if entry:records.append(entry)
    return list(reversed(records))


def source(output,inputs):
    output.mkdir(parents=True,exist_ok=True);salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('salt shape')
    rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];anchors=[];first=[];counts=Counter()
    cache={}
    for row in rows:
        name=row['repository'];repo=Path(inputs[name])
        if core.git(repo,'rev-parse',core.PINS[name]).strip()!=core.PINS[name]:raise ValueError('history revision pin missing')
        # Repository basename is not relied on for source identity.
        output_log=core.git(repo,'log','--follow','--format=COMMIT %H %ct','--name-status',core.PINS[name],'--',row['relative_path'])
        manifest=[];current=row['relative_path'];entry=None
        for line in output_log.splitlines():
            if line.startswith('COMMIT '):
                if entry:manifest.append(entry)
                _,commit,stamp=line.split();entry={'commit':commit,'timestamp':int(stamp),'path':current}
            elif entry and line.startswith('R'):
                fields=line.split('\t')
                if len(fields)==3 and fields[2]==current:entry['path']=fields[2];current=fields[1]
        if entry:manifest.append(entry)
        versions=[]
        for revision in reversed(manifest):
            key=(name,revision['commit'])
            if key not in cache:
                changed=core.git(repo,'diff-tree','--root','--no-commit-id','--name-only','-r',revision['commit']).splitlines()
                cache[key]=sum(bool(re.search(r'(?:^|/)(?:pep-|eip-|erc-)\d+\.(?:rst|md|txt)$',p)) for p in changed)
            text=core.git(repo,'show',revision['commit']+':'+revision['path'])
            parsed,reason=core.parse_document(text,name,salt)
            counts['revisions_scanned']+=1
            if parsed is None:counts['excluded_revision_'+reason]+=1;versions.append(None);continue
            versions.append({**parsed,'bulk':cache[key]>5,'commit':revision['commit']})
        earliest=next((v for v in versions if v is not None),None)
        if earliest is not None:
            first.append({**earliest,'document':row['document'],'relative_path':row['relative_path'],
                          'head':core.PINS[name],'version_scope':'earliest eligible licensed Motivation-bearing version'})
        edits=[]
        for earlier,later in zip(versions,versions[1:]):
            if earlier is None or later is None:edits.append(None);continue
            goal_fraction,_=token_change(earlier['motivation'],later['motivation'])
            rest_fraction,added=token_change(earlier['rest'],later['rest'])
            if later['bulk']:counts['bulk_document_commits_excluded']+=1;edits.append(None);continue
            if goal_fraction==0 and rest_fraction==0:counts['markup_or_whitespace_only_excluded']+=1;edits.append(None);continue
            edits.append({'old_goal':earlier['motivation'],'new_goal':later['motivation'],'goal_fraction':goal_fraction,
                          'added':added,'rest_changed':rest_fraction>0,'author':later['author']})
        for index,edit in enumerate(edits):
            if edit is None or edit['goal_fraction']<.2:continue
            counts['goal_change_anchors']+=1
            before=[v['added'] for v in edits[:index] if v is not None and v['rest_changed'] and v['added']][-3:]
            after=[v['added'] for v in edits[index+1:] if v is not None and v['rest_changed'] and v['added']][:3]
            if not before or not after:counts['no_bilateral_added_text']+=1;continue
            anchors.append({'author':edit['author'],'document':row['document'],'old_goal':edit['old_goal'],
                            'new_goal':edit['new_goal'],'before':before,'after':after,'three_each':len(before)==len(after)==3})
        core.write(output/'PROGRESS.json',{'documents':counts['documents']+1,'total':len(rows)})
        counts['documents']+=1
    core.write(output/'anchors.json',{'anchors':anchors})
    core.write(output/'first-drafts.json',{'documents':first})
    result={'counts':dict(counts),'bilateral_anchors':len(anchors),'three_each_anchors':sum(r['three_each'] for r in anchors),
            'heads':core.PINS,'anchors_sha256':core.sha(output/'anchors.json'),'first_drafts_sha256':core.sha(output/'first-drafts.json'),'source_only':True,
            'scope':'lexical added-text commits in locally complete pinned histories; no final-text comparison'}
    core.write(output/'SOURCE.json',result);return result


def reduce_contrasts(before,after,authors,draws=2000):
    before=np.asarray(before,float);after=np.asarray(after,float);unique,codes=np.unique(authors,return_inverse=True)
    if len(unique)<2:return {'status':'unsupported','anchors':len(before),'authors':len(unique)}
    count=np.bincount(codes);a=np.bincount(codes,weights=after);b=np.bincount(codes,weights=before);rng=np.random.default_rng(core.SEED);samples=[]
    for _ in range(draws):
        w=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique));samples.append([w@(a-b)/(w@count),w@b/(w@count),w@a/(w@count)])
    ci=np.quantile(samples,[.025,.975],axis=0).T.tolist();lo,hi=ci[0]
    verdict='supports' if lo>.02 else 'against' if hi<0 or (lo>=-.02 and hi<=.02) else 'inconclusive'
    if len(unique)<20:verdict='below floor, descriptive'
    return {'status':'ok','anchors':len(before),'authors':len(unique),'after_minus_before':float(np.mean(after-before)),
            'before_contrast':float(before.mean()),'after_contrast':float(after.mean()),'intervals_effect_before_after':ci,'draws':draws,'outcome':verdict}


def analyse(output,inputs,config):
    anchors=json.loads(Path(inputs['anchors']).read_text('utf8'))['anchors'];full=[r for r in anchors if r['three_each']]
    fallback=len(full)<100;selected=anchors if fallback else full
    if not selected:result={'card':'GO2','status':'unsupported','reason':'no bilateral observed-history anchors'}
    else:
        texts=[];slices=[]
        for row in selected:
            before=row['before'][-1:] if fallback else row['before'];after=row['after'][:1] if fallback else row['after']
            start=len(texts);texts.extend([row['old_goal'],row['new_goal'],*before,*after]);slices.append((start,len(before),len(after)))
        unique=list(dict.fromkeys(texts));lookup={value:i for i,value in enumerate(unique)}
        from .week5_go_readers import embeddings
        encoded=embeddings(unique,inputs['encoder_manifest']);vectors=encoded[[lookup[value] for value in texts]];before=[];after=[]
        for start,nb,na in slices:
            direction=vectors[start+1]-vectors[start];before.append(float(np.mean(vectors[start+2:start+2+nb]@direction)));after.append(float(np.mean(vectors[start+2+nb:start+2+nb+na]@direction)))
        result=reduce_contrasts(before,after,[r['author'] for r in selected],config.get('draws',2000))
        result.update(card='GO2',window='one before/one after fallback' if fallback else 'three before/three after',three_each_source_anchors=len(full),
                      scope='alignment with stated revised motivation; before contrast reports the reverse-direction rival')
        if len(selected)<100:result['outcome']='below floor, descriptive'
    core.write(output/'RESULT.json',result);return result


def fixture():
    fraction,added=token_change('we should keep old words','we should add new words')
    assert fraction>=.2 and added=='add new'
    for sign in [-1,0,1]:
        r=reduce_contrasts(np.full(40,.1),np.full(40,.1+sign*.04),[str(i) for i in range(40)],2000)
        assert abs(r['after_minus_before']-sign*.04)<1e-10
    return {'passed':True,'signed_null_author_bootstrap':True,'token_change_and_added_only':True,'draws':2000}


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='prepare':return source(output,inputs)
    if config.get('phase')=='fixture':r=fixture();core.write(output/'FIXTURE.json',r);return r
    return analyse(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='fixture':actual=fixture();name='FIXTURE.json'
    elif config.get('phase')=='prepare':actual=source(output/'independent-replay',inputs);name='SOURCE.json'
    else:actual=analyse(output/'independent-replay',inputs,config);name='RESULT.json'
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('GO2 complete replay differs')
    return {'verified':True,'complete_replay':True}
