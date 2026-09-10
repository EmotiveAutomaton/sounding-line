"""Fail-closed fit/test and reserve boundaries for prepared human-source consumers.

DESIGN CHECK: LESSONS 3-5; I02/X01/X05. NULL: disjoint unrelated units survive;
short shared phrases do not invent author identity. ALTERNATIVE: a copied task,
transitive long overlap, aliased paper, shared writer/stimulus or exposed reserve
is caught before fitting/reading. Consumer inputs are projected evidence and opaque
group IDs, never outcomes. Bands: safe subset with all exclusions recorded, or error.
This module is preparation/evaluation only and must not enter reader capsules.
"""
from collections import defaultdict
import unicodedata
from runners.stage9.common import REPO,digest,file_hash,read


def normalized_evidence(value):
    if isinstance(value,str):
        return ' '.join(unicodedata.normalize('NFKC',value).split())
    if isinstance(value,dict):
        return {k:normalized_evidence(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [normalized_evidence(v) for v in value]
    if value is None or type(value) in (bool,int,float):
        return value
    raise ValueError('unsupported evidence fingerprint type')


def task_copies(fit,test):
    """Require each caller to pass ONLY its registered visible evidence.

    Full task evidence is compared, not isolated words or labels. Other scope and
    projection checks remain the capsule contract's responsibility.
    """
    targets={digest(normalized_evidence(r['evidence'])) for r in test}
    if not targets:raise ValueError('no test evidence')
    kept=[];excluded=[]
    for row in fit:
        if digest(normalized_evidence(row['evidence'])) in targets:
            excluded.append({'key':row['key'],'unit':row['unit'],'reason':'exact normalized complete visible task copied across fit/test'})
        else:kept.append(row)
    return kept,excluded


def disjoint_factors(fit,test,factors):
    if not fit or not test or not factors:
        raise ValueError('both partitions and explicit independent factors required')
    checks={}
    for factor in factors:
        a={r[factor] for r in fit};b={r[factor] for r in test}
        if None in a or None in b:raise ValueError('missing independent factor')
        checks[factor]={'fit_groups':len(a),'test_groups':len(b),'shared_groups':len(a&b)}
    if any(r['shared_groups'] for r in checks.values()):
        raise ValueError('fit/test share a declared source or stimulus factor')
    return checks


class Separation:
    def __init__(self,groups,result,aliases=()):
        self.groups=groups
        self.neighbors=defaultdict(set)
        for edge in result['long_overlap_edges']:
            # Common supplied stimuli are tracked by disjoint_factors, not
            # misrepresented as shared maker identity. Artifact overlaps retain
            # their full conservative transitive separation.
            if any(set(w['roles']) <= {'shared_stimulus'} for w in edge['witnesses']):
                continue
            a,b=edge['groups']
            if a not in groups or b not in groups:raise ValueError('unknown overlap group')
            self.neighbors[a].add(b);self.neighbors[b].add(a)
        for component in aliases:
            if not set(component)<=set(groups):raise ValueError('unknown aliased group')
            for g in component:self.neighbors[g].update(set(component)-{g})

    @classmethod
    def verified(cls,directory):
        completed=read(directory/'COMPLETE.json')
        for name,sha in completed['files'].items():
            if file_hash(directory/name)!=sha:raise ValueError('changed overlap output')
        inputs=read(directory/'INPUTS.json')
        if not inputs or not completed['input_hashes_reverified']:raise ValueError('empty or unverified overlap inputs')
        for name,sha in inputs.items():
            if file_hash(REPO/name)!=sha:raise ValueError('prepared source changed after overlap audit')
        # Verify the actual executed audit code as well as the data closure.
        identity=read(directory/'IDENTITY.json')
        if digest(identity)!=completed['identity_sha256']:raise ValueError('audit identity mismatch')
        for name,sha in identity['sources']['files'].items():
            if file_hash(REPO/name)!=sha:raise ValueError('audit source changed')
        return cls(read(directory/'GROUPS.json'),read(directory/'OVERLAPS.json'),
                   completed['summary']['paper_alias_components'])

    def connected(self,groups):
        groups=set(groups)
        if not groups or not groups<=set(self.groups):raise ValueError('empty or unknown source group set')
        todo=list(groups);found=set(groups)
        while todo:
            for other in self.neighbors[todo.pop()]-found:
                found.add(other);todo.append(other)
        return found

    def filter_fit(self,fit_groups,test_groups):
        fit_groups=set(fit_groups);test_groups=set(test_groups)
        if not fit_groups or not fit_groups<=set(self.groups):raise ValueError('empty or unknown fit groups')
        forbidden=self.connected(test_groups)
        excluded=fit_groups&forbidden
        return sorted(fit_groups-excluded),{'fit_groups':len(fit_groups),'test_groups':len(test_groups),
            'excluded_groups':sorted(excluded),'retained_groups':len(fit_groups-excluded),
            'rule':'exclude whole fitted source groups linked to test by identity or long evidence overlap',
            'claim':'dependency control; connected writers are not asserted to be the same person'}

    def require_reserve(self,groups):
        groups=set(groups);connected=self.connected(groups)
        if any(self.groups[g]['split']!='reserve' or self.groups[g]['previously_exposed'] for g in groups):
            raise ValueError('requested reserve includes exposed or non-reserved groups')
        if any(self.groups[g]['previously_exposed'] or self.groups[g]['split'] in ('pilot','train','development')
               for g in connected):
            raise ValueError('reserve is linked to exposed evidence')
        # An unexamined discovery alias is a reserve-dependent unit, not an
        # independent discovery opportunity. Callers must exclude it before science.
        aliases=sorted(g for g in connected-groups if self.groups[g]['split']=='discovery')
        if aliases:
            raise ValueError('reserve has unreconciled discovery dependencies')
        return {'groups':len(groups),'dependent_reserved_groups':sorted(connected-groups),
                'untouched_status':'source exposure only; no foundation-model memorization guarantee'}

