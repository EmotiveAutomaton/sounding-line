"""Full GO1 grid, dependency-bound readers and sealed CPU quanta.

DESIGN CHECK: all readers use one fixed candidate roster and common full-context
support; Rationale is removed structurally; pilot limits never become samples.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
from . import week5_go as core
from . import week5_go_readers as readers


class Paused(Exception):pass


def requested(output):return any((p/'YIELD_REQUEST.json').exists() for p in [output,output.parent,output.parent.parent])


def prepared_rows(inputs,config):
    rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents']
    if config.get('repository')=='peps':rows=[r for r in rows if r['repository']=='peps']
    if config.get('repository')=='eips':rows=[r for r in rows if r['repository'] in ['eips','ercs']]
    if config.get('version') in ['first','final-matched']:
        first=json.loads(Path(inputs['first_drafts']).read_text('utf8'))['documents'];lookup={r['document']:r for r in first}
        rows=[lookup[r['document']] if config['version']=='first' else r for r in rows if r['document'] in lookup]
    if config.get('field')=='rationale':
        for row in rows:
            path=row['relative_path'];repo=inputs[row['repository']];revision=row.get('commit',row['head'])
            text=core.git(Path(repo),'show',revision+':'+path);_,parts=core.sections(text)
            excluded=[(p['start'],p['subtree_end']) for p in parts if p['normalized'] in ['rationale','copyright','copyright and license','copyright and licence']]
            row['rest']='\n\n'.join(p['heading']+'\n'+p['text'] for p in parts if not any(a<=p['start']<b for a,b in excluded))
    field=config.get('field','motivation');rest=config.get('rest','rest')
    rows=[r for r in rows if r.get(field,'').strip() and r.get(rest,'').strip()]
    roster=core.allocate(rows,config.get('distractors',49),field=field,other_types=config.get('other_types',False))
    if config.get('strict_stratum'):roster=[a for a in roster if not a['other_stratum']]
    return rows,roster


def vector_bank(texts,manifest,output,config):
    output.mkdir(parents=True,exist_ok=True);unique=list(dict.fromkeys(texts));cache={};new=0;began=time.process_time()
    bind={'manifest_sha256':core.sha(manifest),'reader_sha256':core.sha(readers.__file__),'pipeline_sha256':core.sha(__file__)}
    for text in unique:
        key=hashlib.sha256(text.encode()).hexdigest();path=output/(key+'.json')
        if path.exists():
            if core.sha(path)!=json.loads(path.with_suffix('.seal.json').read_text('utf8'))['sha256']:raise ValueError('encoder checkpoint seal changed')
            value=json.loads(path.read_text('utf8'))
            if value['binding']!=bind or value['text_sha256']!=key:raise ValueError('encoder checkpoint binding changed')
            a=np.asarray(value['vector'],np.float32)
            if a.shape!=(384,) or not np.isfinite(a).all() or abs(np.linalg.norm(a)-1)>1e-5:raise ValueError('encoder checkpoint is malformed')
            cache[text]=a
    def saved(text,vector):
        nonlocal new
        key=hashlib.sha256(text.encode()).hexdigest();core.write(output/(key+'.json'),{'binding':bind,'text_sha256':key,'vector':vector.tolist()})
        core.write(output/(key+'.seal.json'),{'sha256':core.sha(output/(key+'.json'))})
        new+=1;core.write(output/'PROGRESS.json',{'cached':len(cache),'new':new,'total':len(unique),'new_cpu_seconds':time.process_time()-began})
        if new+len(cache)<len(unique) and (new>=config.get('max_new_texts',len(unique)) or requested(output) or time.process_time()-began>=config.get('max_cpu_seconds',1e100)):raise Paused()
    if len(cache)==len(unique):return np.asarray([cache[t] for t in texts])
    if requested(output):raise Paused()
    return readers.embeddings(texts,manifest,cache,saved)


def lm_scores(rows,roster,inputs,config,output):
    from .week5_at_scoring import load_model,CausalScorer
    from .week5_at_source import authenticate
    manifest=json.loads(Path(inputs['model_manifest']).read_text('utf8'));selection=Path(inputs['at2_selection']);authenticate(selection)
    result=json.loads((selection/'output/RESULT.json').read_text('utf8'))
    if result.get('card')!='AT2' or not result.get('selection_admissible') or result.get('screening_only') or result.get('selected_model')!=manifest['model']:raise ValueError('complete AT2 selection required')
    model,tokenizer,torch=load_model(manifest);context=int(config['context_length'])
    output.mkdir(parents=True,exist_ok=True);field=config.get('field','motivation');rest=config.get('rest','rest');scores=[];new=0;began=time.process_time()
    bound=hashlib.sha256(json.dumps({'rows':rows,'roster':roster,'manifest':manifest,'context':context,'field':field,'rest':rest,'code':core.sha(__file__)},sort_keys=True).encode()).hexdigest()
    for index,a in enumerate(roster):
        path=output/f'{index:06d}.json'
        if path.exists():
            if core.sha(path)!=json.loads(path.with_suffix('.seal.json').read_text('utf8'))['sha256']:raise ValueError('LM row checkpoint seal changed')
            value=json.loads(path.read_text('utf8'))
            if value['binding']!=bound:raise ValueError('LM row checkpoint binding changed')
        else:
            if new>=config.get('max_new_queries',len(roster)) or requested(output) or time.process_time()-began>=config.get('max_cpu_seconds',1e100):raise Paused()
            prefix=rows[a['query']][rest]+'\n\n';candidates=[rows[j][field] for j in a['candidates']]
            if any(len(tokenizer.encode(prefix+c,add_special_tokens=False))+1>context for c in candidates):values=None
            else:
                values=[]
                for candidate in candidates:
                    # A fresh cache for each likelihood makes resumed rows and
                    # duplicate candidate texts invariant to prior row order.
                    old=CausalScorer(model,tokenizer,torch,context).score('',candidate)
                    conditioned=CausalScorer(model,tokenizer,torch,context).score(prefix,candidate)
                    for r in [old,conditioned]:
                        if r['surprisal_nats']!=sum(r['native_token_nll']):raise ValueError('GO conditional likelihood must be a sum')
                    values.append(old['surprisal_nats']-conditioned['surprisal_nats'])
            value={'binding':bound,'values':values};core.write(path,value);core.write(path.with_suffix('.seal.json'),{'sha256':core.sha(path)});new+=1
            core.write(output/'PROGRESS.json',{'queries':index+1,'total':len(roster),'new_cpu_seconds':time.process_time()-began})
        scores.append(value['values'] if value['values'] is not None else [float('nan')]*len(a['candidates']))
    return np.asarray(scores)


def grid():
    return [{'cell':'GO1','draws':2000},{'cell':'GO1.d9','distractors':9,'draws':200},
            {'cell':'GO1.d99','distractors':99,'strict_stratum':True,'draws':200},
            {'cell':'GO1.peps','repository':'peps','draws':200},{'cell':'GO1.eips','repository':'eips','draws':200},
            {'cell':'GO1.specification','rest':'specification','draws':200},
            {'cell':'GO1.first','version':'first','draws':200},{'cell':'GO1.final-matched','version':'final-matched','draws':200},
            {'cell':'GO1.r','field':'rationale','draws':2000},{'cell':'GO1.d','other_types':True,'draws':2000}]


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True);rows,roster=prepared_rows(inputs,config);phase=config['phase']
    if not roster:
        result={'status':'unsupported','outcome':'below floor, descriptive','documents':len(rows),'scope':'no fixed candidate roster; source counts only'}
        core.write(output/'RESULT.json',result);return result
    if phase=='GO1-score':
        reader=config['reader'];field=config.get('field','motivation');rest=config.get('rest','rest')
        try:
            if reader=='tfidf':scores=core.lexical_scores(rows,roster,field,rest)
            elif reader=='encoder':
                v=vector_bank([r[rest] for r in rows]+[r[field] for r in rows],inputs['encoder_manifest'],output/'vectors',config)
                scores=np.asarray([v[a['query']]@v[[len(rows)+j for j in a['candidates']]].T for a in roster])
            elif reader=='language_model':scores=lm_scores(rows,roster,inputs,config,output/'queries')
            else:raise ValueError('unknown reader')
        except Paused:return {'status':'yielded','reader':reader,'complete_card':False}
        np.save(output/'scores.npy',scores);core.write(output/'ALLOCATION.json',{'allocation':roster})
        core.write(output/'ROWS.json',{'documents':rows})
        result={'reader':reader,'rows':len(roster),'candidate_count':scores.shape[1],'scores_sha256':core.sha(output/'scores.npy'),
                'allocation_sha256':core.sha(output/'ALLOCATION.json'),'rows_sha256':core.sha(output/'ROWS.json'),'complete_card':False}
        core.write(output/'SCORED.json',result);return result
    if phase=='GO1-collect':
        bank={}
        for name,directory in inputs['readers'].items():
            path=Path(directory);receipt=json.loads((path/'SCORED.json').read_text('utf8'))
            for f,k in [('scores.npy','scores_sha256'),('ALLOCATION.json','allocation_sha256'),('ROWS.json','rows_sha256')]:
                if core.sha(path/f)!=receipt[k]:raise ValueError('reader output changed')
            if json.loads((path/'ALLOCATION.json').read_text('utf8'))['allocation']!=roster or json.loads((path/'ROWS.json').read_text('utf8'))['documents']!=rows:raise ValueError('reader candidate/source mismatch')
            bank[name]=np.load(path/'scores.npy',allow_pickle=False)
        if set(bank)!={'tfidf','encoder','language_model'}:raise ValueError('complete primary needs all three reader banks')
        result=readers.collect(rows,roster,bank,config.get('draws',2000));result.update(card=config.get('cell','GO1'),source_variant={k:v for k,v in config.items() if k not in ['phase','draws']})
        core.write(output/'RESULT.json',result);return result
    raise ValueError('GO1 phase is unsupported')


def verify(output:Path,inputs:dict,config:dict):
    actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    name='SCORED.json' if config['phase']=='GO1-score' and actual.get('status')!='unsupported' else 'RESULT.json'
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('complete GO1 replay differs')
    if name=='SCORED.json' and not np.array_equal(np.load(output/'scores.npy'),np.load(output/'independent-replay/scores.npy'),equal_nan=True):raise ValueError('individual reader scores differ')
    return {'verified':True,'complete_replay':True}
