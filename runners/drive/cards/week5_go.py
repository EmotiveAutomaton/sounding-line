"""Week 5 goal-text source, candidate allocation and reader comparisons.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Hide the actual goal section before
reader input, keep first-listed authors together, fix candidate rosters before
scores, and compare against lexical retrieval rather than a chance-only claim.
Constructed unique-token goals verify removal and allocation. Public outputs
contain no raw proposal text, names, handles or individual document scores.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import time
for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[k]="2"
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SEED=20261107
PINS={'peps':'d94bba4a5dff241fd418f30223d3bf05de27a771','eips':'af5ea76669821d1eb8dfc60e3373a0a7fa9a7759','ercs':'47c7f884eb12e110d915b20f7cf0e8077542158b'}
ENCODER='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
ENCODER_REVISION='e8f8c211226b894fcb81acc59f3b34ba3efd5f42'


def write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8')
    for a in range(10):
        try:os.replace(tmp,path);break
        except PermissionError:
            if a==9:raise
            time.sleep(.02*(a+1))


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def git(repo,*args):
    env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,encoding='utf8',errors='strict',env=env,timeout=120)
    if result.returncode:raise ValueError('local pinned git object unavailable or git command refused')
    return result.stdout


def sections(text):
    lines=text.splitlines();starts=[];header={};header_end=0;rst_levels={};fence=False
    markdown=bool(lines and lines[0].strip()=='---')
    if lines and lines[0].strip()=='---':
        end=next((i for i in range(1,len(lines)) if lines[i].strip()=='---'),0)
        for line in lines[1:end]:
            if ':' in line:k,v=line.split(':',1);header[k.strip().lower()]=v.strip()
        header_end=end+1
    else:
        for i,line in enumerate(lines):
            if not line.strip():header_end=i+1;break
            if ':' in line and not line.startswith(' '):k,v=line.split(':',1);header[k.strip().lower()]=v.strip()
    for i in range(header_end,len(lines)):
        line=lines[i]
        if re.match(r'^\s*(```|~~~)',line):fence=not fence;continue
        if fence:continue
        match=re.match(r'^(#{1,6})\s+(.+?)\s*#*$',line)
        if match:starts.append((i,i+1,match.group(2).strip(),len(match.group(1))))
        elif not markdown and i+1<len(lines) and line.strip() and re.fullmatch(r'[=~\-^`:#*+]{3,}',lines[i+1].strip()):
            marker=lines[i+1].strip()[0]
            if marker not in rst_levels:rst_levels[marker]=len(rst_levels)+1
            starts.append((i,i+2,line.strip(),rst_levels[marker]))
    parts=[]
    for j,(start,body,name,level) in enumerate(starts):
        end=starts[j+1][0] if j+1<len(starts) else len(lines)
        subtree_end=next((later[0] for later in starts[j+1:] if later[3]<=level),len(lines))
        parts.append({'heading':name,'normalized':re.sub(r'[^a-z ]','',name.lower()).strip(),
                      'text':'\n'.join(lines[body:end]).strip(),'full_text':'\n'.join(lines[body:subtree_end]).strip(),
                      'start':start,'end':end,'subtree_end':subtree_end,'level':level})
    return header,parts


def parse_document(text,repo,salt):
    header,parts=sections(text)
    motivation=[p for p in parts if p['normalized']=='motivation']
    if not motivation:return None,'no_motivation'
    copyright_text='\n'.join(p['text'] for p in parts if p['normalized'] in ['copyright','copyright and license','copyright and licence'])
    if repo=='peps' and not (re.search(r'public domain|\bCC0\b',copyright_text,re.I)):
        return None,'unapproved_document_license'
    author=header.get('author','').strip()
    if not author:return None,'no_author'
    # Header author syntax is public metadata; hashes, never its literal, are retained.
    first=re.split(r',\s*(?![^<]*>)',author)[0]
    normalized=re.sub(r'<[^>]*>|\([^)]*\)','',first).strip().casefold()
    if not normalized:return None,'empty_first_author'
    ident=hmac.new(salt,('proposal-author:'+normalized).encode(),hashlib.sha256).hexdigest()
    goal='\n\n'.join(p['full_text'] for p in motivation)
    if not goal.strip():return None,'empty_motivation'
    # Remove the entire motivation section, header and copyright. Never reconstruct
    # 'rest' by replacing matching substrings, which can leave a repeated goal copy.
    excluded=[(p['start'],p['subtree_end']) for p in parts if p['normalized'] in ['motivation','copyright','copyright and license','copyright and licence']]
    rest='\n\n'.join(p['heading']+'\n'+p['text'] for p in parts if not any(a<=p['start']<b for a,b in excluded))
    return {'repository':repo,'author':ident,'multi_author':len(re.split(r',\s*(?![^<]*>)',author))>1,
            'type':header.get('type','unknown'),'category':header.get('category',''),
            'status':header.get('status','unknown'),'motivation':goal,'rest':rest,
            'rationale':'\n\n'.join(p['full_text'] for p in parts if p['normalized']=='rationale'),
            'abstract':'\n\n'.join(p['full_text'] for p in parts if p['normalized']=='abstract'),
            'specification':'\n\n'.join(p['full_text'] for p in parts if p['normalized']=='specification'),
            'license':'public-domain/CC0 statement in document' if repo=='peps' else 'CC0 repository',
            'license_statement_sha256':hashlib.sha256(copyright_text.encode()).hexdigest()},None


def source(inputs):
    salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('salt shape')
    rows=[];counts={};seen=set()
    for name in ['peps','eips','ercs']:
        if name not in inputs:continue
        repo=Path(inputs[name]);head=git(repo,'rev-parse','HEAD').strip()
        if head!=PINS[name]:raise ValueError('proposal repository revision mismatch')
        if git(repo,'status','--porcelain').strip():raise ValueError('source checkout is modified')
        if name!='peps' and 'CC0 1.0 Universal' not in (repo/'LICENSE.md').read_text('utf8'):raise ValueError('repository license mismatch')
        folder=repo/('peps' if name=='peps' else 'EIPS' if name=='eips' else 'ERCS')
        files=sorted(folder.glob('*.rst' if name=='peps' else '*.md'))
        counts[name]={'files':len(files),'included':0,'excluded':{}}
        for path in files:
            text=path.read_text('utf8');row,reason=parse_document(text,name,salt)
            if row is not None:
                content=hashlib.sha256((row['motivation']+'\n'+row['rest']).encode()).hexdigest()
                if content in seen:reason='duplicate_content'
                else:
                    seen.add(content);row['document']=f'document_{len(rows):05d}';row['relative_path']=path.relative_to(repo).as_posix();row['source_sha256']=sha(path);row['head']=head
                    rows.append(row);counts[name]['included']+=1;continue
            counts[name]['excluded'][reason]=counts[name]['excluded'].get(reason,0)+1
    return rows,{'repositories':counts,'heads':{name:PINS[name] for name in counts},'documents':len(rows),
                 'first_author_clusters':len({r['author'] for r in rows}),'scope':'current pinned proposal text; Motivation is author-stated rationale, not latent goal truth'}


def allocate(rows,distractors=49,seed=SEED,field='motivation',other_types=False):
    rng=np.random.default_rng(seed);result=[]
    for i,row in enumerate(rows):
        if not row[field].strip():continue
        def stratum(r):return (r['repository'],r['type'],r['category'] if r['repository']!='peps' and r['type']=='Standards Track' else '')
        eligible=[j for j,r in enumerate(rows) if j!=i and r[field].strip() and r['repository']==row['repository']]
        same=[j for j in eligible if stratum(rows[j])==stratum(row)]
        if other_types:same=[j for j in eligible if stratum(rows[j])!=stratum(row)]
        if len(eligible)<distractors:continue
        primary=rng.choice(same,min(distractors,len(same)),replace=False).tolist()
        remainder=[j for j in eligible if j not in primary]
        extra=rng.choice(remainder,distractors-len(primary),replace=False).tolist()
        candidates=[i]+primary+extra; rng.shuffle(candidates)
        result.append({'query':i,'candidates':candidates,'truth_position':candidates.index(i),'other_stratum':len(extra)})
    return result


def lexical_scores(rows,allocation,field='motivation',rest='rest'):
    vectorizer=TfidfVectorizer(lowercase=True,ngram_range=(1,2),min_df=1,sublinear_tf=True)
    texts=[r[rest] for r in rows]+[r[field] for r in rows]
    vectors=vectorizer.fit_transform(texts);scores=[]
    for a in allocation:
        score=cosine_similarity(vectors[a['query']],vectors[[len(rows)+j for j in a['candidates']]]).ravel()
        scores.append(score)
    return np.array(scores)


def encoder_embeddings(texts):
    import torch
    from transformers import AutoModel,AutoTokenizer
    torch.set_num_threads(2)
    tokenizer=AutoTokenizer.from_pretrained(ENCODER,revision=ENCODER_REVISION,local_files_only=True,trust_remote_code=False)
    model=AutoModel.from_pretrained(ENCODER,revision=ENCODER_REVISION,local_files_only=True,trust_remote_code=False).to('cpu').eval()
    values=[]
    with torch.inference_mode():
        for text in texts:
            ids=tokenizer.encode(text,add_special_tokens=False);chunks=[]
            for start in range(0,max(1,len(ids)),126):
                token=tokenizer.prepare_for_model(ids[start:start+126],add_special_tokens=True,return_tensors='pt')
                output=model(**token).last_hidden_state;mask=token['attention_mask'][:,:,None]
                chunks.append((output*mask).sum(dim=1).div(mask.sum(dim=1)).numpy()[0])
            vector=np.mean(chunks,axis=0);norm=np.linalg.norm(vector);values.append(vector/norm if norm else vector)
    return np.asarray(values)


def reader_scores(rows,allocation,reader,config):
    field=config.get('field','motivation');rest=config.get('rest','rest')
    if reader=='tfidf':return lexical_scores(rows,allocation,field,rest)
    if reader=='encoder':
        vectors=encoder_embeddings([r[rest] for r in rows]+[r[field] for r in rows]);return np.array([vectors[a['query']]@vectors[[len(rows)+j for j in a['candidates']]].T for a in allocation])
    if reader=='language_model':
        from .week5_at_scoring import load_model,CausalScorer
        if 'model_manifest' not in config or 'at2_selection' not in config:
            raise ValueError('AT2 selected model and selection receipt are required')
        manifest=json.loads(Path(config['model_manifest']).read_text('utf8'))
        from .week5_at_source import authenticate
        selection_root=Path(config['at2_selection'])
        authenticate(selection_root)
        selection=json.loads((selection_root/'output/RESULT.json').read_text('utf8'))
        if selection.get('card')!='AT2' or not selection.get('selection_admissible',False) or selection.get('screening_only',False) or selection.get('selected_model')!=manifest['model']:
            raise ValueError('AT2 selection does not bind the model manifest')
        model,tok,torch=load_model(manifest);context=int(config['context_length'])
        scorer=CausalScorer(model,tok,torch,context)
        unconditional={};scores=[]
        for a in allocation:
            prefix=rows[a['query']][rest]+'\n\n';candidates=[rows[j][field] for j in a['candidates']]
            # No truncated document silently counts as a full-document reading.
            if any(len(tok.encode(prefix+c,add_special_tokens=False))+1>context for c in candidates):
                scores.append(np.full(len(candidates),np.nan));continue
            values=[]
            for j,candidate in zip(a['candidates'],candidates):
                if j not in unconditional:unconditional[j]=scorer.score('',candidate)['surprisal_nats']
                values.append(unconditional[j]-scorer.score(prefix,candidate)['surprisal_nats'])
            scores.append(values)
        return np.asarray(scores)
    raise ValueError('unknown GO reader')


def correctness(scores,allocation):
    # A fixed random-order roster gives unbiased exact-tie resolution via first maximum.
    return np.array([np.argmax(score)==a['truth_position'] for score,a in zip(scores,allocation)],float)


def compare(rows,allocation,score_bank,draws=2000):
    if not allocation:raise ValueError('empty candidate roster')
    original_count=len(allocation)
    supported=np.logical_and.reduce([np.isfinite(v).all(axis=1) for v in score_bank.values()])
    allocation=[a for a,use in zip(allocation,supported) if use]
    score_bank={name:values[supported] for name,values in score_bank.items()}
    if not allocation:return {'status':'unsupported','reason':'no full-document common reader support','documents':0,'source_queries':original_count}
    names=sorted(score_bank);correct={n:correctness(score_bank[n],allocation) for n in names}
    people=np.array([rows[a['query']]['author'] for a in allocation]);unique,code=np.unique(people,return_inverse=True)
    counts=np.bincount(code);sums={n:np.bincount(code,weights=c,minlength=len(unique)) for n,c in correct.items()}
    if len(unique)<2:return {'status':'unsupported','documents':len(allocation),'authors':len(unique)}
    rng=np.random.default_rng(SEED);samples={n:[] for n in names};differences={n:[] for n in names if n!='tfidf'}
    for _ in range(draws):
        w=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique));denom=w@counts
        values={n:float(w@sums[n]/denom) for n in names}
        for n in names:samples[n].append(values[n])
        for n in differences:differences[n].append(values[n]-values['tfidf'])
    result={'status':'ok','documents':len(allocation),'source_queries':original_count,'context_unsupported_queries':original_count-len(allocation),'authors':len(unique),'draws':draws,
            'chance':1/len(allocation[0]['candidates']),'other_stratum_distractor_share':sum(a['other_stratum'] for a in allocation)/(len(allocation)*(len(allocation[0]['candidates'])-1)),
            'readers':{n:{'accuracy':float(correct[n].mean()),'interval':np.quantile(samples[n],[.025,.975]).tolist(),
                         'above_chance':float(correct[n].mean()-1/len(allocation[0]['candidates'])),
                         'above_chance_interval':(np.quantile(samples[n],[.025,.975])-1/len(allocation[0]['candidates'])).tolist()} for n in names},
            'gain_over_lexical':{n:{'estimate':float(correct[n].mean()-correct['tfidf'].mean()),'interval':np.quantile(v,[.025,.975]).tolist()} for n,v in differences.items()},
            'primary_ready':'language_model' in names,'scope':'current documents; author-stated Motivation retrieval; descriptive'}
    if result['primary_ready']:
        lo,hi=result['gain_over_lexical']['language_model']['interval']
        result['outcome']='supports' if lo>.05 else 'against' if hi<0 or (lo>=-.05 and hi<=.05) else 'inconclusive'
        result['next_branch']='GO1.r' if any(v['interval'][0]>.05 for v in result['gain_over_lexical'].values()) else 'GO1.d'
    return result


def fixture():
    rst='PEP: 99\nAuthor: Example Person\nType: Standards Track\n\nMotivation\n----------\nSECRETGOAL\n\nSpecification\n-------------\nbody word\n\nCopyright\n---------\nThis document has been placed in the public domain.\n'
    row,reason=parse_document(rst,'peps',b'x'*32);assert reason is None
    assert 'SECRETGOAL' not in row['rest'] and row['motivation']=='SECRETGOAL'
    rows=[]
    for i in range(60):rows.append({**row,'motivation':f'unique{i}','rest':f'unique{i}','document':str(i),'author':str(i)})
    roster=allocate(rows);scores=lexical_scores(rows,roster)
    assert correctness(scores,roster).mean()==1.
    assert all(len(set(a['candidates']))==50 for a in roster)
    return {'passed':True,'goal_section_hidden':True,'candidate_roster_unique':True,'lexical_known_answer':True}


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True);phase=config.get('phase','prepare')
    if phase=='fixture':a=fixture();write(output/'FIXTURE.json',a);return a
    if phase=='prepare':
        rows,a=source(inputs);write(output/'documents.json',{'documents':rows});a['documents_sha256']=sha(output/'documents.json');write(output/'SOURCE.json',a);return a
    if phase=='GO1-score':
        rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];roster=allocate(rows,config.get('distractors',49),field=config.get('field','motivation'),other_types=config.get('other_types',False))
        if not roster:raise ValueError('no eligible proposal candidate allocations')
        scores=reader_scores(rows,roster,config['reader'],config);np.save(output/'scores.npy',scores);write(output/'ALLOCATION.json',{'allocation':roster})
        a={'reader':config['reader'],'rows':len(roster),'candidate_count':scores.shape[1],'scores_sha256':sha(output/'scores.npy'),'allocation_sha256':sha(output/'ALLOCATION.json'),'complete_card':False};write(output/'SCORED.json',a);return a
    if phase=='GO1-collect':
        rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];bank={};roster=None
        for name,directory in inputs['readers'].items():
            path=Path(directory);a=json.loads((path/'ALLOCATION.json').read_text('utf8'))['allocation']
            if roster is not None and a!=roster:raise ValueError('different reader candidate rosters')
            roster=a;bank[name]=np.load(path/'scores.npy',allow_pickle=False)
        if 'tfidf' not in bank:raise ValueError('lexical comparison required')
        result=compare(rows,roster,bank,config.get('draws',2000));write(output/'RESULT.json',result);return result
    raise ValueError('unimplemented GO phase')


def verify(output:Path,inputs:dict,config:dict):
    phase=config.get('phase','prepare')
    if phase=='fixture':
        if fixture()!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('fixture replay')
    elif phase=='prepare':
        rows,_=source(inputs)
        if rows!=json.loads((output/'documents.json').read_text('utf8'))['documents']:raise ValueError('all-source projection replay')
    else:
        replay=output/'verify';result=execute(replay,inputs,config)
        target='SCORED.json' if phase=='GO1-score' else 'RESULT.json';expected=json.loads((output/target).read_text('utf8'))
        if result!=expected:raise ValueError('GO numerical replay')
    return {'verified':True,'phase':phase,'full_replay':True}
