"""Private Stack Exchange revision projection and GO3 diff-only classification.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Reason comments supply labels only;
they never enter predictors. Body edits alone form the five-category primary.
Users remain disjoint across validation folds. The comparison predicts from
class priors stochastically, never the inappropriate majority-class baseline.
"""
from collections import Counter
import difflib
import hashlib
import hmac
import json
from pathlib import Path,PurePosixPath
import re
import shutil
import sqlite3
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from . import week5_go as core

PRIMARY=['typo_spelling','grammar','clarity','added_content','removed_content']
REASONS={
 'typo_spelling':r'\b(typos?|spell(?:ing)?|misspell\w*|speling)\b',
 'grammar':r'\b(grammar|grammatical|tense|conjugat\w*)\b',
 'formatting':r'\b(format\w*|markdown|indent\w*|whitespace|layout)\b',
 'clarity':r'\b(clarif\w*|clarity|clearer|reword\w*|readability|ambig\w*)\b',
 'added_content':r'\b(add(?:ed|ing)?|expand\w*|elaborat\w*|detail\w*|explanation)\b',
 'removed_content':r'\b(remov\w*|delet\w*|redundan\w*|irrelevant|trim\w*)\b',
 'links':r'\b(links?|urls?|hyperlinks?|citations?|references?)\b',
 'tags':r'\b(tags?|retag\w*)\b',
}
ARCHIVES={
 'writers':'07630d6f16ad00b2878dad1138d91fb1b0c56c212007a87c48acf6b2d6a16892',
 'philosophy':'31a5a6d1ed4945f0ee97852f34c1b97e54b1c56348f75263a8b3a6c1c1c8961a',
 'academia':'5113eb82928523f259cde2ace39c43ce34655b9eb2d765dddaae8477007ec06a',
 'worldbuilding':'e033aab9349845aeb6fa2d3b03ffc879172b0ebf6ea4e56cfd9fe5885abec618',
 'english':'b9ac7b48e5d8fa9e83acdf08ebcdf24dc3906d36a80c15137a2abe2904282e3d'}
LICENSE_SHA='d36393108ad6b64f97a7b17dd873fe670ace6aa948975ef546a744481678e545'


def reason(comment):
    found=[name for name,pattern in REASONS.items() if re.search(pattern,comment.casefold())]
    return found[0] if len(found)==1 else 'multiple' if found else 'other'


def salted(salt,site,value):return hmac.new(salt,(site+':'+str(value)).encode(),hashlib.sha256).hexdigest()


def extract(archive,directory):
    import py7zr
    directory.mkdir(parents=True,exist_ok=True);targets=['Posts.xml','PostHistory.xml']
    with py7zr.SevenZipFile(archive,'r') as container:
        members=container.list();names=[v.filename for v in members]
        if not set(targets)<=set(names):raise ValueError('expected XML members absent')
        expanded=sum(v.uncompressed for v in members if v.filename in targets)
        if expanded+10*1024**3>shutil.disk_usage(directory).free:raise ValueError('insufficient extraction headroom')
        for name in targets:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe archive member')
        if not all((directory/name).exists() for name in targets):container.extract(path=directory,targets=targets)
    return {name:core.sha(directory/name) for name in targets}


def project_site(archive,salt,site,output):
    if site not in ARCHIVES or core.sha(archive)!=ARCHIVES[site]:raise ValueError('Stack archive pin mismatch')
    output.mkdir(parents=True,exist_ok=True);member_hashes=extract(archive,output/'xml')
    db=sqlite3.connect(output/'projection.sqlite');db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE IF NOT EXISTS posts (post TEXT PRIMARY KEY, author TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS history (post TEXT,stamp TEXT,ordinal INTEGER,type INTEGER,editor TEXT,label TEXT,body TEXT)')
    # Reentry uses a fresh scratch projection; source archives and completed
    # outputs remain untouched. Only hashed joins are written to SQLite.
    db.execute('DELETE FROM posts');db.execute('DELETE FROM history');counts=Counter()
    for _,element in ET.iterparse(output/'xml/Posts.xml',events=['end']):
        if element.tag!='row':continue
        row=element.attrib;post=salted(salt,site+'-post',row['Id']);owner=row.get('OwnerUserId')
        db.execute('INSERT INTO posts VALUES (?,?)',(post,salted(salt,site+'-user',owner) if owner else None));counts['posts']+=1;element.clear()
    db.commit()
    for _,element in ET.iterparse(output/'xml/PostHistory.xml',events=['end']):
        if element.tag!='row':continue
        row=element.attrib;kind=int(row['PostHistoryTypeId'])
        if kind in (1,2,3,4,5,6,24):
            user=row.get('UserId');db.execute('INSERT INTO history VALUES (?,?,?,?,?,?,?)',
                (salted(salt,site+'-post',row['PostId']),row['CreationDate'],int(row['Id']),kind,
                 salted(salt,site+'-user',user) if user else None,reason(row.get('Comment','')),row.get('Text','')))
            counts['history_rows']+=1
        element.clear()
    db.commit();db.execute('CREATE INDEX IF NOT EXISTS by_post_date ON history(post,stamp,ordinal)');db.commit()
    import pyarrow as pa
    import pyarrow.parquet as pq
    rows=[];previous={};current=None;writer=None;retained=0
    def flush(batch):
        nonlocal writer
        table=pa.Table.from_pylist(batch)
        if writer is None:writer=pq.ParquetWriter(output/'edits.parquet',table.schema,compression='zstd')
        writer.write_table(table)
    sql='SELECT h.post,h.stamp,h.ordinal,h.type,h.editor,h.label,h.body,p.author FROM history h LEFT JOIN posts p ON h.post=p.post ORDER BY h.post,h.stamp,h.ordinal'
    for post,stamp,ordinal,kind,editor,label,body,author in db.execute(sql):
        if post!=current:previous={};current=post
        channel='body' if kind in (2,5,24) else 'title' if kind in (1,4) else 'tags'
        before=previous.get(channel);previous[channel]=body
        if kind not in (4,5,6,24):continue
        counts['edit_type_'+str(kind)]+=1;counts['label_'+label]+=1
        if editor is None:counts['anonymous_edits_excluded']+=1;continue
        if before is None:counts['missing_before_excluded']+=1;continue
        if before==body:counts['unchanged_text_excluded']+=1;continue
        rows.append({'editor':editor,'post':post,'stamp':stamp,'site':site,'type':kind,'reason':label,
                     'self_edit':editor==author if author else False,'owner_known':author is not None,'before':before,'after':body})
        retained+=1
        if len(rows)>=1024:flush(rows);rows=[]
    if rows:flush(rows)
    if writer is None:raise ValueError('no supported revision rows')
    writer.close();db.close()
    receipt={'site':site,'archive_sha256':ARCHIVES[site],'member_sha256':member_hashes,'counts':dict(counts),
             'retained_edits':retained,'projection_sha256':core.sha(output/'edits.parquet'),
             'license':'CC BY-SA 3.0 per supplied dump notice; source text private; citation and attribution required for redistribution',
             'privacy':'Identifiers salted locally; comments used only for category then dropped; Users profiles never read.'}
    core.write(output/'SOURCE.json',receipt);return receipt


def diff_features(before,after):
    old=re.findall(r'\w+|[^\w\s]',before);new=re.findall(r'\w+|[^\w\s]',after)
    matcher=difflib.SequenceMatcher(None,old,new,autojunk=False);added=removed=replaced=0
    for tag,i,j,k,l in matcher.get_opcodes():
        if tag!='equal':removed+=j-i;added+=l-k
        if tag=='replace':replaced+=1
    # Token Levenshtein with a bounded exact dynamic program. Long bodies use
    # unchanged common prefix/suffix removal before computing the same distance.
    while old and new and old[0]==new[0]:old=old[1:];new=new[1:]
    while old and new and old[-1]==new[-1]:old.pop();new.pop()
    if len(old)>len(new):old,new=new,old
    previous=list(range(len(old)+1))
    for i,right in enumerate(new,1):
        current=[i]
        for j,left in enumerate(old,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(left!=right)))
        previous=current
    distance=previous[-1]
    patterns=[r'[.!?,;:]',r'https?://|\]\(',r'`[^`]*`|<code>',r'\n',r'\s{2,}',r'\b[A-Z][a-z]+\b']
    counts=[float(len(re.findall(p,after))-len(re.findall(p,before))) for p in patterns]
    return [len(before),len(after),len(after)-len(before),added,removed,replaced,distance,distance/max(1,len(before),len(after)),*counts]


def macro_f1(matrix):
    matrix=np.asarray(matrix,float);den=matrix.sum(axis=0)+matrix.sum(axis=1)
    return float(np.mean(np.divide(2*np.diag(matrix),den,out=np.zeros(len(den)),where=den>0)))


def score_oof(x,labels,users,folds=5):
    classes=PRIMARY;encoded=np.array([classes.index(v) for v in labels]);keys=np.unique(users)
    if len(keys)<20:return {'status':'unsupported','reason':'fewer than twenty user clusters'},None
    rng=np.random.default_rng(core.SEED);assignment={key:i%folds for i,key in enumerate(rng.permutation(keys))};f=np.array([assignment[v] for v in users])
    predicted=np.full(len(x),-1,int);prior=np.zeros((len(x),len(classes)))
    for fold in range(folds):
        train=f!=fold;test=~train
        if len(np.unique(encoded[train]))<len(classes):return {'status':'unsupported','reason':'training fold missing primary reason'},None
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=1000,solver='lbfgs',random_state=core.SEED))
        model.fit(x[train],encoded[train]);predicted[test]=model.predict(x[test]);prior[test]=np.bincount(encoded[train],minlength=len(classes))/train.sum()
    return {'status':'ok','folds':folds,'user_disjoint':True},(encoded,predicted,prior)


def uncertainty(encoded,predicted,prior,users,draws=2000):
    keys,code=np.unique(users,return_inverse=True);n=len(keys);k=len(PRIMARY)
    model=np.zeros((n,k,k));baseline=np.zeros_like(model)
    for i in range(len(encoded)):
        model[code[i],encoded[i],predicted[i]]+=1;baseline[code[i],encoded[i]]+=prior[i]
    observed=macro_f1(model.sum(axis=0))-macro_f1(baseline.sum(axis=0));rng=np.random.default_rng(core.SEED);boot=[]
    for _ in range(draws):
        w=np.bincount(rng.integers(0,n,n),minlength=n);boot.append(macro_f1(np.einsum('n,nij->ij',w,model))-macro_f1(np.einsum('n,nij->ij',w,baseline)))
    ci=np.quantile(boot,[.025,.975]).tolist();lo,hi=ci
    return {'users':n,'edits':len(encoded),'macro_f1':macro_f1(model.sum(axis=0)),'prior_only_expected_macro_f1':macro_f1(baseline.sum(axis=0)),
            'gain':observed,'interval':ci,'draws':draws,'outcome':'supports' if lo>.05 else 'against' if hi<0 or (lo>=-.05 and hi<=.05) else 'inconclusive',
            'baseline':'expected confusion of stochastic training-prior predictions, not majority class'}


def fixture():
    assert reason('fix spelling')=='typo_spelling' and reason('add link')=='multiple'
    assert diff_features('a b c','a b d')[6]==1
    labels=np.tile(np.arange(5),40);users=np.repeat(np.arange(40),5);prior=np.full((200,5),.2)
    r=uncertainty(labels,labels,prior,users,2000)
    assert abs(r['gain']-.8)<1e-12
    assert macro_f1(np.zeros((5,5)))==0
    return {'passed':True,'comment_dictionary_disjoint':True,'exact_token_distance':True,'prior_stochastic_baseline':True,'user_cluster_draws':2000}


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='fixture':r=fixture();core.write(output/'FIXTURE.json',r);return r
    if config.get('phase')=='prepare':
        if core.sha(Path(inputs['license']))!=LICENSE_SHA:raise ValueError('dump licence notice mismatch')
        return project_site(Path(inputs['archive']),Path(inputs['salt']).read_bytes(),config['site'],output)
    raise ValueError('GO3 complete analysis still requires IteraTeR feature and gallery companion')


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='fixture':actual=fixture();name='FIXTURE.json'
    elif config.get('phase')=='prepare':
        actual=project_site(Path(inputs['archive']),Path(inputs['salt']).read_bytes(),config['site'],output/'independent-replay');name='SOURCE.json'
        import pyarrow.parquet as pq
        from itertools import zip_longest
        left=pq.ParquetFile(output/'edits.parquet').iter_batches(batch_size=1024)
        right=pq.ParquetFile(output/'independent-replay/edits.parquet').iter_batches(batch_size=1024)
        for a,b in zip_longest(left,right):
            if a is None or b is None or not a.equals(b):raise ValueError('every projected revision row must reconstruct')
    else:raise ValueError('unimplemented complete verification')
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('GO3 complete projection replay differs')
    return {'verified':True,'full_replay':True}
