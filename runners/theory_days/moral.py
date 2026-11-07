"""Complete-pair Moral Machine source preparation and frozen B2 comparison.

DESIGN CHECK: LESSONS 2-5. Source orphans and duplicated scenarios are not choices.
Equal exposure and fair-coin worlds must not support differential rigidity.
No prefix becomes a scientific population; homogeneous samples retain uncertainty.
"""
from pathlib import Path
import gzip,io,json,sqlite3,tarfile,time
import numpy as np
import pandas as pd
from runners.stage14.common import freeze,read,filehash
from .backlog_intake import moral_header

COLUMNS=['ResponseID','ExtendedSessionID','UserID','Intervention','Saved','AttributeLevel','ScenarioType','ScenarioTypeStrict']
LEVELS={'Species':{'Hoomans':1,'Humans':1,'Pets':0},'Gender':{'Male':0,'Males':0,'Female':1,'Females':1},'Fitness':{'Fit':1,'Fat':0}}
UPSERT='''INSERT INTO pairs VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(rid) DO UPDATE SET
 n=pairs.n+1, saved=pairs.saved+excluded.saved, interventions=pairs.interventions+excluded.interventions,
 chosen=pairs.chosen+excluded.chosen, levels=pairs.levels+excluded.levels,
 bad=pairs.bad+excluded.bad+(pairs.usr!=excluded.usr OR pairs.session!=excluded.session),
 dim=CASE WHEN pairs.dim=excluded.dim THEN pairs.dim ELSE '' END,
 positive=pairs.positive+excluded.positive'''


def rows(frame):
    for rid,session,user,intervention,saved,level,kind,strict in frame[COLUMNS].itertuples(index=False,name=None):
        valid=intervention in ('0','1') and saved in ('0','1') and bool(rid and session and user)
        iv=int(intervention) if intervention in ('0','1') else 0;s=int(saved) if saved in ('0','1') else 0
        dim=kind if kind==strict and level in LEVELS.get(kind,{}) else ''
        value=LEVELS[dim][level] if dim else 0
        yield (rid,user,session,1,s,iv,s*(1-iv),value,int(not valid),dim,s*value)


def prepare(source,db_path,outpath,max_rows=None):
    schema=moral_header(source);db=sqlite3.connect(db_path)
    try:
        db.execute('PRAGMA journal_mode=OFF');db.execute('PRAGMA synchronous=OFF');db.execute('PRAGMA cache_size=-65536');db.execute('PRAGMA temp_store=FILE')
        db.execute('CREATE TABLE pairs(rid TEXT PRIMARY KEY,usr TEXT,session TEXT,n INT,saved INT,interventions INT,chosen INT,levels INT,bad INT,dim TEXT,positive INT) WITHOUT ROWID')
        count=0;start=time.process_time()
        with tarfile.open(source,'r:gz') as archive:
            entry=next(iter(archive))
            with archive.extractfile(entry) as stream:
                for frame in pd.read_csv(stream,usecols=COLUMNS,dtype=str,keep_default_na=False,chunksize=100000,nrows=max_rows):
                    db.executemany(UPSERT,rows(frame));db.commit();count+=len(frame)
                consumed=stream.tell()
        census=dict(rows=count,consumed_source_bytes=consumed,source_expanded_bytes=schema['expanded_bytes'],prefix_only=max_rows is not None)
        census['responses']=db.execute('SELECT count(*) FROM pairs').fetchone()[0]
        census['orphans']=db.execute('SELECT count(*) FROM pairs WHERE n=1').fetchone()[0]
        census['duplicated_responses']=db.execute('SELECT count(*) FROM pairs WHERE n>2').fetchone()[0]
        good='n=2 AND saved=1 AND interventions=1 AND bad=0'
        census['complete_valid_pairs']=db.execute('SELECT count(*) FROM pairs WHERE '+good).fetchone()[0]
        census['source_cpu_seconds']=time.process_time()-start
        if max_rows is not None:return census
        query=f'''SELECT usr,dim,count(*),sum(positive),count(DISTINCT session) FROM (
           SELECT usr,session,dim,positive FROM pairs WHERE {good} AND levels=1 AND dim!=''
           UNION ALL SELECT usr,session,'Intervention' AS dim,chosen AS positive FROM pairs WHERE {good})
           GROUP BY usr,dim ORDER BY usr,dim'''
        users=0;common=0;bydim={};current=None;record={}
        with Path(outpath).open('wb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as zipped:
                def emit(user,values):
                    nonlocal users,common
                    if user is None:return
                    users+=1
                    for d,x in values.items():
                        if x[0]>=3:bydim[d]=bydim.get(d,0)+1
                    good_user=all(values.get(d,[0])[0]>=3 for d in (*LEVELS,'Intervention')) and values.get('Intervention',[0,0,0])[2]>=2
                    common+=int(good_user)
                    zipped.write((json.dumps(dict(user=user,dimensions=values,eligible=good_user),sort_keys=True)+'\n').encode())
                for user,dim,n,pos,sessions in db.execute(query):
                    if user!=current:emit(current,record);current=user;record={}
                    record[dim]=[n,pos,sessions]
                emit(current,record)
        census.update(fingerprints=users,common_returning_fingerprints=common,three_scenario_fingerprints=bydim,source_case_pass=common>=1000)
        return census
    finally:db.close()


def contrast(hist,n,draws=2000):
    values=np.array([((i&1)>0)+((i&2)>0)-((i&4)>0)-((i&8)>0) for i in range(16)],dtype=float)/2
    hist=np.asarray(hist,dtype=np.int64);point=float(hist@values/n)
    if np.count_nonzero(hist)==1:
        radius=np.sqrt(2*np.log(40)/n);ci=[max(-1.,point-radius),min(1.,point+radius)];method='bounded_mean_Hoeffding'
    else:
        rng=np.random.default_rng(20261106);boot=rng.multinomial(n,hist/n,size=draws)@values/n
        ci=np.quantile(boot,[.025,.975]).tolist();method='fingerprint_cluster_percentile'
    verdict='supports' if ci[0]>.05 else 'against' if ci[1]<0 or (ci[0]>=-.05 and ci[1]<=.05) else 'inconclusive'
    return dict(difference=point,interval=ci,interval_method=method,verdict=verdict)


def analyze(path,draws=2000):
    rng=np.random.default_rng(20261106);hist=np.zeros(16,dtype=np.int64);n=0;rates=np.zeros(4);allrates=np.zeros(4);chance=np.zeros(4)
    dims=['Species','Intervention','Gender','Fitness']
    with gzip.open(path,'rt',encoding='utf8') as f:
        for line in f:
            record=json.loads(line)
            if not record['eligible']:continue
            v=record['dimensions'];k=min(v[d][0] for d in dims);mask=0
            for j,d in enumerate(dims):
                count,positive,_=v[d];chosen=rng.hypergeometric(positive,count-positive,k)
                never=chosen in (0,k);mask|=int(never)<<j;rates[j]+=never
                allrates[j]+=positive in (0,count);chance[j]+=2.**(1-count)
            hist[mask]+=1;n+=1
    if n<1000:return dict(status='design cannot test',common_fingerprints=n,required=1000)
    return dict(status='complete',common_fingerprints=n,primary=contrast(hist,n,draws),
        equal_exposure_rates=dict(zip(dims,(rates/n).tolist())),all_observed_rates=dict(zip(dims,(allrates/n).tolist())),
        coin_expectations=dict(zip(dims,(chance/n).tolist())),draws=draws)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    source=Path(inputs['source']['path']);assert filehash(source)==inputs['source']['sha256']
    if config['phase']=='analysis':
        result=analyze(source,config.get('draws',2000));freeze(output/'SCIENCE.json',result);return result
    result=prepare(source,output/'source.sqlite',output/'PRIVATE_COUNTS.jsonl.gz',config.get('max_rows'))
    freeze(output/'SOURCE.json',result);return dict(status='complete',scientific_effect_computed=False)


def verify(output,inputs,config):
    output=Path(output);source=Path(inputs['source']['path']);assert filehash(source)==inputs['source']['sha256']
    if config['phase']=='analysis':assert analyze(source,config.get('draws',2000))==read(output/'SCIENCE.json')
    else:
        result=prepare(source,output/'verify.sqlite',output/'VERIFY_COUNTS.jsonl.gz',config.get('max_rows'));prior=read(output/'SOURCE.json')
        result.pop('source_cpu_seconds');prior.pop('source_cpu_seconds');assert result==prior
        if not config.get('max_rows'):assert filehash(output/'VERIFY_COUNTS.jsonl.gz')==filehash(output/'PRIVATE_COUNTS.jsonl.gz')
    return dict(verified=True,complete_recalculation=True)
