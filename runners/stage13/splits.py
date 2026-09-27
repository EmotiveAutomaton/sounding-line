"""Connected source identities and near duplicates, before outcomes.

DESIGN CHECK: LESSONS 2-5. NULL: cross-split copies never count as independent.
ALTERNATIVE: disjoint source components retain their provided partition. Exact
and candidate near duplicates join transitively; conflicts quarantine rather
than leak. Missed approximate duplicates remain a disclosed audit limitation.
"""
from __future__ import annotations
import hashlib
import re
from collections import defaultdict
from .common import digest


class Union:
    def __init__(self): self.parent={}
    def find(self,x):
        self.parent.setdefault(x,x)
        if self.parent[x]!=x:self.parent[x]=self.find(self.parent[x])
        return self.parent[x]
    def join(self,a,b):
        a,b=self.find(a),self.find(b)
        self.parent[max(a,b)]=min(a,b)


def normalized(text): return ' '.join(re.findall(r'\w+',text.lower()))
def shingles(text):
    words=normalized(text).split()
    return {int.from_bytes(hashlib.blake2b(' '.join(words[i:i+5]).encode(),digest_size=8).digest(),'big') for i in range(max(1,len(words)-4))}


def components(sources):
    """LSH candidate search (64 minhashes, 16 bands); exact Jaccard >= .85 joins.

    sources: {identity: {text, split}}. No model prediction or target enters this.
    """
    union=Union();exact={};buckets=defaultdict(list);sets={};links=[]
    mask=(1<<64)-1
    for key in sorted(sources):
        union.find(key);text=sources[key]['text'];norm=normalized(text)
        h=digest(norm)
        if h in exact:union.join(key,exact[h]);links.append([key,exact[h],'exact'])
        exact[h]=key;s=shingles(text);sets[key]=s
        # Independent affine minhashes under a fixed prime, deterministic.
        signature=[min(((x*(2*i+1000003)+i*104729)%18446744073709551557) for x in s) for i in range(64)]
        candidates=set()
        for i in range(16): candidates.update(buckets[(i,tuple(signature[4*i:4*i+4]))])
        for other in sorted(candidates):
            t=sets[other]
            if min(len(s),len(t))/max(len(s),len(t))>=.85 and len(s&t)/len(s|t)>=.85:
                union.join(key,other);links.append([key,other,'near-jaccard-0.85'])
        for i in range(16): buckets[(i,tuple(signature[4*i:4*i+4]))].append(key)
    roots={k:union.find(k) for k in sources};splits=defaultdict(set)
    for k,root in roots.items():splits[root].add(sources[k]['split'])
    conflicts={r for r,partitions in splits.items() if len(partitions)!=1}
    return roots,conflicts,links


def partition(source_split,unit):
    if source_split=='test':return 'reserve'
    if source_split=='train':return 'train'
    if source_split=='dev':return 'calibration' if int(digest(unit)[:8],16)%2 else 'development'
    raise ValueError('unknown source split')
