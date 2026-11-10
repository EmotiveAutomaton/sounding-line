"""V1 split-half individual directions, inherited choice-shuffle controls.

DESIGN CHECK: LESSONS 3-5. Candidate PCA is blind to choices. The focal
annotator never enters either population or country prior. Whole conversations
stay in one half; every null refits all directions on its actual shuffled labels.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week3_alignment_stats as old
from . import week3_alignment_features as feature
from . import week5_bk_ca1_features as bounded
from . import week5_go as core

SEED=20261102


def allocation(rows,clusters,membership):
    people=sorted({r['writer'] for r in rows});groups={}
    for group in ('mandatory','random'):
        for person in membership[group]:
            if person in groups:raise ValueError('sample groups overlap')
            groups[person]=group
    if set(groups)!=set(people):raise ValueError('sample membership differs')
    halves=np.zeros(len(rows),int);details={}
    for person in people:
        indices=[i for i,r in enumerate(rows) if r['writer']==person]
        country={rows[i]['country'] for i in indices}
        if len(country)!=1:raise ValueError('annotator country is not constant')
        conv=sorted({rows[i]['conversation'] for i in indices})
        if len(conv)<2:raise ValueError('annotator has fewer than two conversations')
        seed=int.from_bytes(hashlib.sha256((str(SEED)+person).encode()).digest()[:8],'big')
        order=np.random.default_rng(seed).permutation(conv);by={str(c):i%2 for i,c in enumerate(order)}
        for i in indices:halves[i]=by[rows[i]['conversation']]
        counts=Counter(clusters[rows[i]['prompt']] for i in indices)
        ties=sorted(k for k,v in counts.items() if v==max(counts.values()))
        cluster=int(np.random.default_rng(seed+1).choice(ties))
        details[person]={'country':next(iter(country)),'group':groups[person],'cluster':cluster,
                         'half_comparisons':[int(sum(halves[i]==h for i in indices)) for h in (0,1)]}
    return people,halves,details


def one_person(x,choices,owners,countries,halves,person):
    own=owners==person;country=countries[np.flatnonzero(own)[0]];result=[]
    # Such a person cannot have a same-country comparator either. Preserve the
    # absence explicitly; do not invent a country prior from the focal person.
    if not np.any((countries==country)&~own):return None
    for half in (0,1):
        train=(halves==half)&~own;local=train&(countries==country);target=(halves==half)&own
        if not train.any() or not local.any() or not target.any():raise ValueError('leave-annotator-out prior unsupported')
        pop=old.fit(x[train],choices[train],penalty=1.)
        prior=old.fit(x[local],choices[local],prior=pop,penalty=10.)
        beta=old.fit(x[target],choices[target],prior=prior,penalty=10.)
        result.append(beta.tolist())
    return result


def contrast(profiles,details):
    result=[];counts=Counter()
    for person in sorted(details):
        value=details[person];peers=[w for w in sorted(details) if w!=person and
                                   all(details[w][k]==value[k] for k in ('country','group','cluster'))]
        group=value['group'];counts[(group,'total')]+=1
        if not peers:counts[(group,'no_comparator')]+=1;continue
        a,b=np.asarray(profiles[person],float);norm=np.linalg.norm(a)*np.linalg.norm(b)
        if norm<=1e-14:counts[(group,'zero_direction')]+=1;continue
        own=float(a@b/norm);between=[]
        for w in peers:
            c,d=np.asarray(profiles[w],float)
            if min(np.linalg.norm(c),np.linalg.norm(d))<=1e-14:
                raise ValueError('matched comparator has zero direction; fixed comparator support fails')
            between.extend([float(a@d/(np.linalg.norm(a)*np.linalg.norm(d))),float(b@c/(np.linalg.norm(b)*np.linalg.norm(c)))])
        gain=own-float(np.mean(between))
        if abs(gain)<1e-12:gain=0.
        result.append({'writer':person,'group':group,'own_cosine':own,'matched_cosine':float(np.mean(between)),
                       'gain':gain,'comparators':len(peers)})
    return result,{g:{k:counts[(g,k)] for k in ('total','no_comparator','zero_direction')} for g in ('mandatory','random')}


def summary(real,controls,draws=2000):
    records,counts=real;answer={}
    for gi,group in enumerate(('mandatory','random')):
        selected=[r for r in records if r['group']==group];people=[r['writer'] for r in selected]
        if not people:
            answer[group]={'state':'below floor, descriptive','annotators':0,'exclusions':counts[group]};continue
        values=np.array([r['gain'] for r in selected]);banks=[]
        for rows,_ in controls:
            lookup={r['writer']:r['gain'] for r in rows if r['group']==group}
            if set(lookup)!=set(people):raise ValueError('V1 control changed supported annotators')
            banks.append(float(np.mean([lookup[w] for w in people])))
        rng=np.random.default_rng(SEED+gi);boot=np.array([values[rng.integers(0,len(values),len(values))].mean() for _ in range(draws)])
        ci=np.quantile(boot,[.025,.975]).tolist();point=float(values.mean())
        p=float((1+np.sum(np.array(banks)>=point-1e-12))/(len(banks)+1))
        state='below floor, descriptive' if len(values)<20 else 'supports' if ci[0]>0 else 'against' if ci[1]<0 else 'inconclusive'
        answer[group]={'state':state,'annotators':len(values),'mean_cosine_excess':point,'cluster_95_interval':ci,
                       'own_cosine':float(np.mean([r['own_cosine'] for r in selected])),
                       'matched_cosine':float(np.mean([r['matched_cosine'] for r in selected])),
                       'within_annotator_choice_permutation_p':p,'permutation_draws':len(banks),
                       'control_pass':p<.05,'bootstrap_draws':draws,'exclusions':counts[group],
                       'interval_scope':'annotator resampling of paired gains with the frozen comparator reference held fixed'}
    return answer


def source(inputs,config):
    report,root,rows,_=feature.source(inputs)
    if report.get('variant')!='CA1.s1' and not config.get('fixture'):raise ValueError('frozen CA1.s1 required')
    membership=json.loads((root/'PRIVATE_SAMPLE.json').read_text('utf8'))
    features,fr=feature.bind(inputs,'features')
    if (features.get('card')!='CA1-features' or features.get('mode')!='full' or
        (not config.get('fixture') and (features.get('execution_only') or features.get('constructed_only')))):
        raise ValueError('full freshly verified CA1 representations required')
    if features['input_hashes']['prepared_summary']!=core.sha(inputs['prepared_summary']):raise ValueError('CA1 source mismatch')
    for name,h in features['output_hashes'].items():
        if core.sha(fr/name)!=h:raise ValueError('CA1 complete feature output changed')
    index=json.loads((fr/'INDEX.json').read_text('utf8'))
    if index['comparison_indices']!=list(range(len(rows))):raise ValueError('partial comparison features')
    if not config.get('fixture') and (len(membership['mandatory'])!=836 or len(membership['random'])!=200):
        raise ValueError('original CA1.s1 sample groups required')
    return rows,membership,index,np.load(fr/'EMBEDDINGS.npy',allow_pickle=False)


def run(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    allowed={'fixture','permutations','draws','max_new_fits','max_wall_seconds'}
    if set(config)-allowed:raise ValueError('unknown V1 configuration')
    permutations=int(config.get('permutations',200));draws=int(config.get('draws',2000))
    if not config.get('fixture') and (permutations!=200 or draws!=2000):raise ValueError('complete primary uncertainty/control bank required')
    rows,membership,index,embeddings=source(inputs,config)
    binding={'inputs':{k:core.sha(v) for k,v in inputs.items()},'module_sha256':core.sha(__file__),
             'original_stats_sha256':core.sha(old.__file__),'seed':SEED,'draws':draws,'permutations':permutations,
             'fixture':bool(config.get('fixture'))}
    bp=output/'BINDINGS.json'
    if bp.exists() and json.loads(bp.read_text('utf8'))!=binding:raise ValueError('V1 frozen binding changed')
    core.write(bp,binding)
    with threadpool_limits(limits=2):x,pca=old.candidate_features(rows,embeddings,index['text_indices'],seed=old.SEED)
    core.write(output/'PCA.json',pca)
    people,halves,details=allocation(rows,index['prompt_clusters'],membership)
    owners=np.array([r['writer'] for r in rows]);countries=np.array([r['country'] for r in rows]);observed=np.array([r['choice'] for r in rows],int)
    start=time.monotonic();cpu=time.process_time();new=0;banks=[]
    for bank in range(permutations+1):
        choices=observed.copy()
        if bank:
            rng=np.random.default_rng(np.random.SeedSequence([SEED,bank]))
            for p in people:
                ix=np.flatnonzero(owners==p);choices[ix]=rng.permutation(choices[ix])
        profiles={}
        for number,person in enumerate(people):
            path=output/'fits'/f'{bank:03d}-{number:04d}.json';seal=path.with_suffix('.seal.json')
            if seal.exists():
                saved=json.loads(seal.read_text('utf8'))
                if saved['binding']!=binding or saved['sha256']!=core.sha(path):raise ValueError('V1 direction checkpoint changed')
                profiles[person]=json.loads(path.read_text('utf8'))
            else:
                if new>=config.get('max_new_fits',10**12) or bounded.wanted(output) or time.monotonic()-start>=config.get('max_wall_seconds',900):
                    return {'status':'yielded','phase':'V1_directions','bank':bank,'annotator_index':number,
                            'full_fits':(permutations+1)*len(people),'new_fits':new,'new_cpu_seconds':time.process_time()-cpu}
                with threadpool_limits(limits=2):value=one_person(x,choices,owners,countries,halves,person)
                core.write(path,value);core.write(seal,{'binding':binding,'sha256':core.sha(path)});profiles[person]=value;new+=1
            core.write(output/'PROGRESS.json',{'phase':'V1_directions','bank':bank,'annotators_completed':number+1,
                                             'annotators_total':len(people),'new_fits':new,'new_cpu_seconds':time.process_time()-cpu})
        scores=contrast(profiles,details);core.write(output/f'bank-{bank:03d}.json',scores);banks.append(scores)
    result={'card':'V1','scope':'CA1.s1 separate support-selected and seeded groups; no causal or identification claim',
            'groups':summary(banks[0],banks[1:],draws),'binding':binding,'complete_primary':True,
            'model':'candidate-only PCA16; conditional logit ridge1/10/10; focal annotator absent from both priors',
            'halves':'whole conversations in seeded random order, alternating halves; no chronology claim',
            'references':'all other annotators of same country, sample group and dominant prompt cluster; seeded cluster ties'}
    core.write(output/'RESULT.json',result);return result


def execute(output,inputs,config):return run(output,inputs,config)


def verify(output,inputs,config):
    output=Path(output);result=run(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('V1 full independent replay differs')
    return {'verified':True,'all_fits_permutations_and_bootstrap_recomputed':True}
