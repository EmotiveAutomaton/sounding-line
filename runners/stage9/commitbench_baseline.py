"""Repository-held-out diff/description baseline with explicit surface rivals.

DESIGN CHECK: LESSONS 2-5; H06/X03/X05. NULL: message vocabulary, paths or length
can recover a candidate without semantic understanding; all remain scored rivals.
ALTERNATIVE: planted diff-description correspondence is learnable and survives
whole-repository holdout. Four real candidate descriptions, complete and distinct,
same primary language, other repositories, nearest message word count then fixed
content hash; the same menu/order serves every arm. No fabricated purpose labels.
Bands: invalid projection or overlap fails; complete development estimates remain
descriptive. Discovery/reserve are not loaded. No individual accumulation.
"""
from collections import Counter
import math
import re
import time
from runners.stage9.common import ROOT,REPO,closure,digest,file_hash,freeze,read,distribution
from runners.stage9.commitbench import parse_diff,visible
from runners.stage9.scoring import log_score,paired_interval


def words(text):
    text=re.sub(r'([a-z])([A-Z])',r'\1 \2',text)
    return re.findall(r'[a-z][a-z0-9]*',text.casefold())


def language(row):
    return next((x for x in row['languages'] if x in ('py','js','java','rb','go','php')),row['languages'][0])


def menu(row,pool):
    candidates={row['message']:row}
    eligible=[r for r in pool if r['unit']!=row['unit'] and r['message']!=row['message'] and language(r)==language(row)]
    ordered=sorted(eligible,key=lambda r:(abs(len(words(r['message']))-len(words(row['message']))),
                                         digest({'menu':row['diff'],'candidate':r['message']})))
    for r in ordered:
        candidates.setdefault(r['message'],r)
        if len(candidates)==4:break
    if len(candidates)!=4:return None
    descriptions=sorted(candidates,key=lambda m:digest({'diff':row['diff'],'description':m,'order':'v1'}))
    return {'evidence':visible(row,descriptions),'truth':str(descriptions.index(row['message'])),
            'candidate_keys':[candidates[m]['key'] for m in descriptions]}


def pair_features(diff,message):
    parsed=parse_diff(diff);change='\n'.join(parsed['added']+parsed['removed'])
    code=set(words(change));allcode=set(words(diff));paths=set(words(' '.join(parsed['paths'])));tokens=words(message);m=set(tokens)
    def overlap(s):return len(m&s)/max(1,len(m))
    return {'change_overlap':overlap(code),'all_overlap':overlap(allcode),'path_overlap':overlap(paths),
            'change_jaccard':len(m&code)/max(1,len(m|code)),
            'message_log_words':math.log1p(len(tokens)),
            'length_ratio':len(tokens)/max(1,len(words(change))),
            'added_ratio':len(parsed['added'])/max(1,len(parsed['added'])+len(parsed['removed'])),
            'size_message_interaction':math.log1p(len(tokens))*math.log1p(len(change)),
            'first_word:'+tokens[0] if tokens else 'empty_message':1.}


def normalize(scores):
    if len(scores)!=4 or not all(math.isfinite(float(x)) for x in scores):raise ValueError('invalid candidate scores')
    top=max(scores);exp=[math.exp(x-top) for x in scores];total=sum(exp)
    return distribution({str(i):.99*x/total+.01/4 for i,x in enumerate(exp)})


def run():
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    started=time.time();prepared=ROOT/'private/prepared/commitbench-v1';out=ROOT/'private/pilot-baseline/commitbench-v1'
    identity_source=read(prepared/'IDENTITY.json');complete=read(prepared/'COMPLETE.json')
    if complete['identity_sha256']!=digest(identity_source) or complete['source_count_matches'] is not True:raise ValueError('preparation invalid')
    paths={s:prepared/s/'RECORDS.json' for s in ('train','development')}
    for s,p in paths.items():
        if file_hash(p)!=complete['files'][s+'/RECORDS.json']:raise ValueError('prepared split changed')
    test=read(paths['development']);attempted=read(paths['train'])
    if {r['unit'] for r in attempted}&{r['unit'] for r in test}:raise ValueError('repository leakage')
    messages={r['message'] for r in test};diffs={r['content_sha256'] for r in test}
    training=[r for r in attempted if r['message'] not in messages and r['content_sha256'] not in diffs]
    train_menus=[(r,menu(r,training)) for r in training];test_menus=[(r,menu(r,test)) for r in test]
    source=closure([REPO/'runners/stage9'/n for n in ('commitbench.py','commitbench_baseline.py','scoring.py','common.py')])
    identity={'prepared':digest(identity_source),'split_files':{s:file_hash(p) for s,p in paths.items()},'sources':source,
              'candidates':'same-language real full messages, different repositories, closest word count then content hash; same order every arm',
              'forecast':'C1 balanced logistic pair classifier, normalized exp(logit), explicit .01 uniform mixture',
              'rivals':'uniform, fixed4x added/removed vocabulary overlap, fixed4x path overlap, learned message/size/filename features',
              'scope':'development only, repository held out, no independent H06 claim'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    x=[];y=[];units=[]
    for row,m in train_menus:
        if m is None:continue
        for i,candidate in enumerate(m['evidence']['candidate_descriptions']):
            x.append(pair_features(m['evidence']['diff'],candidate));y.append(int(str(i)==m['truth']));units.append(row['unit'])
    if not x or len(set(y))!=2:raise ValueError('empty or one-class training task')
    counts=Counter(units);weights=[len(units)/len(counts)/counts[u] for u in units]
    vec=DictVectorizer();matrix=vec.fit_transform(x)
    model=LogisticRegression(C=1.,solver='lbfgs',class_weight='balanced',max_iter=1000,random_state=902109)
    model.fit(matrix,y,sample_weight=weights)
    # Surface-only rival excludes all content overlap except filenames. It is fitted
    # on the same candidate pairs and labels, not selected by test performance.
    surface=lambda f:{k:v for k,v in f.items() if k not in ('change_overlap','all_overlap','change_jaccard')}
    sv=DictVectorizer();sx=sv.fit_transform([surface(f) for f in x]);sm=LogisticRegression(C=1.,solver='lbfgs',class_weight='balanced',max_iter=1000,random_state=902109)
    sm.fit(sx,y,sample_weight=weights)
    predictions=[];truths={};menus=[]
    for row,m in test_menus:
        if m is None:continue
        fs=[pair_features(m['evidence']['diff'],c) for c in m['evidence']['candidate_descriptions']]
        ps={'learned_pair':normalize(model.decision_function(vec.transform(fs))),
            'message_size_path':normalize(sm.decision_function(sv.transform([surface(f) for f in fs]))),
            'lexical_overlap':normalize([4*f['change_overlap'] for f in fs]),
            'filename_overlap':normalize([4*f['path_overlap'] for f in fs]),'uniform':{str(i):.25 for i in range(4)}}
        predictions.append({'key':row['key'],'unit':row['unit'],'probabilities':ps});truths[row['key']]=m['truth']
        menus.append({'key':row['key'],'candidate_keys':m['candidate_keys'],'evidence':m['evidence']})
    freeze(out/'PREDICTIONS.json',predictions);freeze(out/'MENUS.json',menus);freeze(out/'TRUTH.json',truths)
    scored=[{'key':r['key'],'unit':r['unit'],'scores':{a:log_score(p,truths[r['key']]) for a,p in r['probabilities'].items()}} for r in predictions]
    freeze(out/'SCORES.json',scored)
    contrasts={a+'_over_'+b:paired_interval([r|{'difference':r['scores'][a]-r['scores'][b]} for r in scored])
               for a,b in [('learned_pair','uniform'),('learned_pair','lexical_overlap'),('learned_pair','message_size_path'),
                           ('lexical_overlap','uniform'),('filename_overlap','uniform'),('message_size_path','uniform')]}
    result={'identity_sha256':digest(identity),'elapsed_seconds':time.time()-started,'completed_at':time.time(),
            'fit_attempts':len(attempted),'fit_duplicate_exclusions':len(attempted)-len(training),
            'fit_candidate_failures':sum(m is None for _,m in train_menus),'fit_questions':len(x)//4,
            'fit_repositories':len(set(units)),'test_attempts':len(test),'test_questions':len(predictions),
            'test_candidate_failures':sum(m is None for _,m in test_menus),'test_repositories':len({r['unit'] for r in predictions}),
            'test_languages':dict(Counter(language(r) for r,m in test_menus if m is not None)),
            'contrasts':contrasts,'disposition':'DESCRIPTIVE','reserve_read':False,
            'output_hashes':{n:file_hash(out/n) for n in ('PREDICTIONS.json','MENUS.json','TRUTH.json','SCORES.json')},
            'limits':['candidate-menu task not free message generation','surface correspondence is not historical intent',
                      'release noncanonical diffs excluded by hunk gate','full H06 capsule and cross-source closure owed']}
    freeze(out/'COMPLETE.json',result);freeze(ROOT/'intake/COMMITBENCH_BASELINE.json',result)
    return result


if __name__=='__main__':print(run())
