"""Complete GO3 classifier, frozen textures and three-role habit companion.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. External IteraTeR labels only train a
feature extractor; held-out Stack users determine all validation folds. The
reason comment never enters diff features. No user-habit claim without donor
separation, fixed-gallery support, a conditional null and paired uncertainty.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,re,time
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from . import week5_go_revisions as source
from . import week5_go as core

ITERATER_SHA='0b1d1dbe74e2a68495cd0770746899c354cf6787450fc6b14b7ee1f95914eb4c'


def levenshtein(a,b):
    """Exact Myers bit-vector edit distance, with sequence elements as symbols."""
    if not a:return len(b)
    if len(a)>len(b):a,b=b,a
    if not a:return len(b)
    masks={}
    for i,item in enumerate(a):masks[item]=masks.get(item,0)|(1<<i)
    positive=(1<<len(a))-1;negative=0;score=len(a);high=1<<(len(a)-1);limit=(1<<len(a))-1
    for item in b:
        equal=masks.get(item,0);xv=equal|negative;xh=(((equal&positive)+positive)^positive)|equal
        ph=negative|~(xh|positive);mh=positive&xh
        if ph&high:score+=1
        if mh&high:score-=1
        ph=(ph<<1)|1;mh<<=1
        positive=(mh|~(xv|ph))&limit;negative=ph&xv
    return score


def features(before,after):
    # Reuse all frozen feature definitions, substituting an independently tested
    # exact algorithm for the potentially quadratic Python distance loop.
    import difflib
    old=re.findall(r'\w+|[^\w\s]',before);new=re.findall(r'\w+|[^\w\s]',after)
    added=removed=replaced=0
    for tag,i,j,k,l in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if tag!='equal':removed+=j-i;added+=l-k
        if tag=='replace':replaced+=1
    distance=levenshtein(old,new);patterns=[r'[.!?,;:]',r'https?://|\]\(',r'`[^`]*`|<code>',r'\n',r'\s{2,}',r'\b[A-Z][a-z]+\b']
    counts=[float(len(re.findall(p,after))-len(re.findall(p,before))) for p in patterns]
    return [len(before),len(after),len(after)-len(before),added,removed,replaced,distance,distance/max(1,len(before),len(after)),*counts]


def external_intent(path):
    path=Path(path)
    if core.sha(path)!=ITERATER_SHA:raise ValueError('IteraTeR published training file pin differs')
    rows=[json.loads(line) for line in path.open(encoding='utf8') if line.strip()]
    x=np.asarray([features(r['before_sent'],r['after_sent']) for r in rows],float);y=[r['labels'] for r in rows]
    model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=1000,random_state=core.SEED))
    model.fit(x,y)
    return model,{'published_split':'train only','rows':len(rows),'labels':dict(Counter(y)),'source_sha256':ITERATER_SHA,
                  'label_scope':'released annotator revision-intent categories, not writers own goal survey'}


def prepare_features(output,inputs):
    import pyarrow.parquet as pq
    import pyarrow as pa
    model,report=external_intent(inputs['iterater_train']);output.mkdir(parents=True,exist_ok=True)
    schema=None;writer=None;count=0;bound={}
    for directory in inputs['sites']:
        path=Path(directory)/'edits.parquet';bound[str(path)]=core.sha(path)
        for batch in pq.ParquetFile(path).iter_batches(batch_size=512):
            frame=batch.to_pandas();x=np.asarray([features(a,b) for a,b in zip(frame.before,frame.after)],float)
            probability=model.predict_proba(x)
            saved=frame.drop(columns=['before','after']).copy()
            for j in range(x.shape[1]):saved[f'diff_{j}']=x[:,j]
            for j,label in enumerate(model.classes_):saved['intent_'+label]=probability[:,j]
            table=pa.Table.from_pandas(saved,preserve_index=False)
            if writer is None:writer=pq.ParquetWriter(output/'features.parquet',table.schema,compression='zstd')
            writer.write_table(table);count+=len(frame)
            core.write(output/'PROGRESS.json',{'feature_rows':count})
    if writer is None:raise ValueError('no revision features')
    writer.close();report.update(rows_projected=count,inputs=bound,features_sha256=core.sha(output/'features.parquet'))
    core.write(output/'FEATURES.json',report);return report


def habit_profiles(rows,assignment=None):
    grouped=defaultdict(list)
    for row in rows:
        writer=row['editor'] if assignment is None else assignment[row['row']]
        grouped[writer].append(row)
    result={}
    for writer,edits in grouped.items():
        posts=defaultdict(list)
        for row in edits:posts[row['post']].append(row)
        ordered=sorted(posts,key=lambda post:min(r['stamp'] for r in posts[post]));halves=[[],[]]
        for i,post in enumerate(ordered):halves[i%2].extend(posts[post])
        if all(halves):result[writer]=halves
    return result


def habit_accuracy(rows,folds,rosters,assignment=None):
    profiles=habit_profiles(rows,assignment);scores={};context={}
    categories=list(source.REASONS)+['other','multiple'];index={v:i for i,v in enumerate(categories)}
    for role in range(3):
        donors=[r for r in rows if folds[r['editor']]==role];means={}
        blocks=defaultdict(list)
        for row in donors:blocks[(row['site'],row['post'])].append(row)
        for key,block in blocks.items():means[key]=np.bincount([index[r['reason']] for r in block],minlength=len(categories))/len(block)
        for writer,candidates in rosters[role].items():
            if writer not in profiles or any(c not in profiles for c in candidates):return None
            real_vectors=[];ctx_vectors=[]
            for who,half in [(writer,0)]+[(c,1) for c in candidates]:
                records=profiles[who][half]
                if any((r['site'],r['post']) not in means for r in records):return None
                real_vectors.append(np.bincount([index[r['reason']] for r in records],minlength=len(categories))/len(records))
                ctx_vectors.append(np.mean([means[(r['site'],r['post'])] for r in records],axis=0))
            for bank,target in [(real_vectors,scores),(ctx_vectors,context)]:
                distance=np.sum((np.asarray(bank[1:])-bank[0])**2,axis=1);minimum=distance.min();ties=np.isclose(distance,minimum,atol=1e-12,rtol=0)
                target[writer]=float(ties[candidates.index(writer)]/ties.sum())
    return scores,context


def habits(frame,draws=2000,permutations=1000,output=None,config=None):
    data=frame[['editor','post','site','stamp','reason']].copy();data['row']=np.arange(len(data));rows=data.to_dict('records');profiles=habit_profiles(rows)
    eligible=sorted(profiles);order=np.random.default_rng(core.SEED).permutation(eligible);folds={str(w):i%3 for i,w in enumerate(order)}
    rows=[r for r in rows if r['editor'] in folds];rosters={};rng=np.random.default_rng(core.SEED+1)
    for role in range(3):
        gallery=[w for w in eligible if folds[w]!=role];probes=[w for w in eligible if folds[w]==(role+1)%3]
        if len(gallery)<30:return {'status':'unsupported','reason':'fewer than thirty fixed non-donor gallery users','eligible_users':len(eligible)}
        rosters[role]={w:[w]+rng.choice([g for g in gallery if g!=w],29,replace=False).tolist() for w in probes}
    result=habit_accuracy(rows,folds,rosters)
    if result is None:return {'status':'unsupported','reason':'fixed galleries lack independent same-post donor support','eligible_users':len(eligible)}
    real,ctx=result;keys=sorted(real);a=np.array([real[w] for w in keys]);b=np.array([ctx[w] for w in keys]);null=[]
    config={} if config is None else config
    binding=hashlib.sha256(json.dumps({'rows':rows,'draws':draws,'permutations':permutations,'code':core.sha(__file__)},sort_keys=True).encode()).hexdigest()
    if output is not None:
        output.mkdir(parents=True,exist_ok=True);checkpoint=output/'permutations.json'
        if checkpoint.exists():
            saved=json.loads(checkpoint.read_text('utf8'))
            if saved['binding']!=binding or core.sha(checkpoint)!=json.loads((output/'permutations.seal.json').read_text('utf8'))['sha256']:raise ValueError('habit permutation checkpoint changed')
            null=saved['null']
    old=len(null);started=time.process_time()
    blocks=defaultdict(list)
    for row in rows:blocks[(row['site'],row['post'],folds[row['editor']])].append(row)
    for permutation in range(len(null),permutations):
        rng=np.random.default_rng(np.random.SeedSequence([core.SEED,permutation,91]));assignment={}
        for block in blocks.values():
            for row,user in zip(block,rng.permutation([r['editor'] for r in block])):assignment[row['row']]=user
        value=habit_accuracy(rows,folds,rosters,assignment)
        if value is None:return {'status':'unsupported','reason':'fixed gallery support lost under conditional reassignment','draw':permutation,'eligible_users':len(eligible)}
        null.append(float(np.mean(list(value[0].values()))))
        if output is not None:
            from .week5_go1_pipeline import requested,Paused
            pause=len(null)-old>=config.get('max_new_permutations',permutations) or requested(output) or time.process_time()-started>=config.get('max_cpu_seconds',1e100)
            if len(null)%10==0 or pause or len(null)==permutations:
                core.write(checkpoint,{'binding':binding,'null':null});core.write(output/'permutations.seal.json',{'sha256':core.sha(checkpoint)})
                core.write(output/'PROGRESS.json',{'permutations':len(null),'total':permutations,'new_cpu_seconds':time.process_time()-started})
            if pause and len(null)<permutations:raise Paused()
    rng=np.random.default_rng(core.SEED+2);boot=[float(np.mean((a-b)[rng.integers(0,len(a),len(a))])) for _ in range(draws)];ci=np.quantile(boot,[.025,.975]).tolist();p=float((1+sum(v>=a.mean()-1e-12 for v in null))/(permutations+1))
    return {'status':'ok','users':len(keys),'gallery':30,'real_accuracy':float(a.mean()),'context_accuracy':float(b.mean()),'difference_interval':ci,
            'conditional_reassignments':permutations,'one_sided_p':p,'paired_draws':draws,'passes':bool(p<.05 and ci[0]>0),
            'context':'same-post independent donors; all fixed gallery support required'}


def classify(frame,config):
    d=frame.loc[frame.type.isin([5,24])&frame.reason.isin(source.PRIMARY)].copy()
    if config.get('self_only'):d=d.loc[d.self_edit&d.owner_known]
    if config.get('site'):d=d.loc[d.site.eq(config['site'])]
    columns=[c for c in d if c.startswith('diff_') or (c.startswith('intent_') and not config.get('without_iterater'))]
    status,bank=source.score_oof(d[columns].to_numpy(float),d.reason.to_numpy(),d.editor.to_numpy())
    if bank is None:
        if len(d) and len(d.reason.unique())>=2:
            model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=1000,random_state=core.SEED))
            model.fit(d[columns].to_numpy(float),d.reason)
            prediction=model.predict(d[columns].to_numpy(float));matrix=np.zeros((5,5))
            for a,b in zip(d.reason,prediction):matrix[source.PRIMARY.index(a),source.PRIMARY.index(b)]+=1
            status.update(pooled_resubstitution_macro_f1=source.macro_f1(matrix),outcome='below floor, descriptive',
                          fallback_scope='pooled descriptive fit on the same observations; not held-out accuracy',edits=len(d),users=d.editor.nunique())
        else:status.update(outcome='below floor, descriptive',category_counts=d.reason.value_counts().to_dict(),edits=len(d),users=d.editor.nunique())
        return status
    result=source.uncertainty(*bank,d.editor.to_numpy(),draws=config.get('draws',2000));result.update(status='ok',feature_columns=columns,folds=5)
    return result


def grid():
    return [{'cell':'GO3','phase':'GO3','draws':2000},{'cell':'GO3.self','phase':'GO3','self_only':True,'draws':200},
            {'cell':'GO3.no-iterater','phase':'GO3','without_iterater':True,'draws':200}]+[
            {'cell':'GO3.'+site,'phase':'GO3','site':site,'draws':200} for site in source.ARCHIVES]


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='features':return prepare_features(output,inputs)
    frame=pd.read_parquet(inputs['features']);result=classify(frame,config)
    if not any(k in config for k in ['self_only','site','without_iterater']):
        from .week5_go1_pipeline import Paused
        try:result['habit_companion']=habits(frame,config.get('draws',2000),config.get('permutations',1000),output/'habits',config)
        except Paused:return {'status':'yielded','complete_card':False}
    result['card']='GO3';result['scope']='comment-stated editing reason categories; retrospective and descriptive'
    core.write(output/'RESULT.json',result);return result


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='features':
        actual=prepare_features(output/'independent-replay',inputs);name='FEATURES.json'
    else:actual=execute(output/'independent-replay',inputs,config);name='RESULT.json'
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('GO3 full numerical replay differs')
    return {'verified':True,'complete_replay':True}
