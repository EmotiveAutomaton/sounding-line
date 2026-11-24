"""Timing facts for LGH3. Membership is restricted to the earlier held-out groups."""
from bisect import bisect_left,bisect_right
import csv
from pathlib import Path
import re
from xml.etree import ElementTree as ET
import numpy as np
from runners.drive.sealed.week7_lgh1 import FEATURES,between,mixture
from runners.drive.cards.week6_sealed_support_v1 import write_tables

def ami_speech_starts(bundle,meeting,roster,assignments,people):
    result=[]
    for channel in roster:
        _,agent=assignments[channel]
        person=people[meeting,agent]
        prefix=f'{meeting}.{agent}'
        words=list(ET.fromstring(bundle.read(f'words/{prefix}.words.xml')))
        index={w.get('{http://nite.sourceforge.net/}id'):i for i,w in enumerate(words)}
        for segment in ET.fromstring(bundle.read(f'segments/{prefix}.segments.xml')):
            timed=[]
            for link in segment:
                href=link.get('href','')
                if not href:continue
                ids=re.findall(r'id\(([^)]+)\)',href)
                if len(ids) not in (1,2) or any(k not in index for k in ids):
                    raise ValueError('Unbound AMI segment word references')
                for w in words[index[ids[0]]:index[ids[-1]]+1]:
                    if w.tag.split('}')[-1]=='w' and (w.text or '').strip() and w.get('starttime'):
                        t=float(w.get('starttime'))
                        if np.isfinite(t):timed.append(t)
            if timed:result.append(dict(speaker=person,start=min(timed)))
    return result

def contextual(marks,speech,start,end):
    if not end>start:raise ValueError('Invalid meeting duration')
    by_actor={}
    for s in speech:by_actor.setdefault(s['speaker'],[]).append(s['start'])
    for times in by_actor.values():times.sort()
    ordered=sorted((m['start'],i,m['speaker']) for i,m in enumerate(marks))
    times=[row[0] for row in ordered]
    values=[]
    for m in marks:
        t=m['start'];a=m['speaker']
        prior=ordered[bisect_left(times,t-3):bisect_left(times,t)]
        near=ordered[bisect_left(times,t-5):bisect_right(times,t+5)]
        own=by_actor.get(a,[])
        i=bisect_left(own,m['end'])
        values.append((any(actor!=a for _,_,actor in prior),len({actor for _,_,actor in near})>=3,
                       i<len(own) and own[i]<=m['end']+2,t>=start+2*(end-start)/3))
    return values

def context_tables(features,metadata,out,original):
    from hashlib import sha256
    # Both memberships and table bytes must reproduce the original release.
    fractions=out/'group_tables/fractions.csv'
    if not fractions.is_file():
        if (original/'group_tables/fractions.csv').exists():raise ValueError('Changed support')
        return 'previous release check withheld groups'
    for f in (original/'group_tables').glob('*.csv'):
        if sha256(f.read_bytes()).digest()!=sha256((out/'group_tables'/f.name).read_bytes()).digest():
            raise ValueError('LGH1 replay differs')
    x=np.asarray(features,float)
    good=np.flatnonzero(np.isfinite(x).all(axis=1))
    rng=np.random.default_rng(2026112205)
    train,test=np.array_split(rng.permutation(good),2)
    z=(x-x[train].mean(axis=0))/x[train].std(axis=0)
    g=mixture(z[train]).predict(z[test])+1
    people=np.array([metadata[i]['speaker'] for i in test])
    with fractions.open() as f:levels={int(v['component']):int(v['n']) for v in csv.DictReader(f)}
    catalog={'component_context':[],'context_shuffles':[]}
    n=len(set(people))
    for j in range(4):
        y=np.array([metadata[i]['context'][j] for i in test],float)
        if len(np.unique(g))>=2:
            null=[between(rng.permutation(y),g) for _ in range(200)]
            catalog['context_shuffles'].append(dict(fact=j+1,fraction_explained=between(y,g),shuffle_95=np.quantile(null,.95),n=n))
        for label,npersons in levels.items():
            mask=g==label
            if len(set(people[mask]))!=npersons:raise ValueError('Component roster mismatch')
            row=dict(fact=j+1,component=label,rate=float(y[mask].mean()),n=npersons)
            row.update(zip(FEATURES,x[test[mask]].mean(axis=0)))
            catalog['component_context'].append(row)
    path=out/'new_tables';path.mkdir()
    return write_tables(path,catalog)
