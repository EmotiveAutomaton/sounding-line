"""Exact original-law subset of the already exposed discarded collection pool.

DESIGN CHECK: C05/C07/X01/X08/X11; LESSONS3--5 and CONTROLS6.
NULL: secondary or unknown laws, missing earlier worlds, relabeled scientific
inputs and changed domain counts cannot masquerade as original-law exposure.
ALTERNATIVE: preserve every complete eligible original-law example and its
unchanged earlier works; preassign the same deterministic half within each domain.
Bands: exact discarded input contract, or refusal before collection/model loading.
This is a timing fixture, not new scientific data or an original-expert trained arm.
"""
import copy
from collections import Counter

from .common import digest
from .recipes import SECONDARY_BY_ROLE
from .matching import mixture_keys

COUNTS={'essay':16,'workshop_doc':14}
ASSIGNED=15


def original_pool(pool):
    """Selection reads law identity and complete lineage, never reader outcomes."""
    required={'candidate_examples','private_worlds','split','original_pool_sha256'}
    if (not isinstance(pool,dict) or set(pool)!=required or pool['split']!='pilot'
            or len(pool['candidate_examples'])!=64
            or not isinstance(pool['original_pool_sha256'],str)
            or len(pool['original_pool_sha256'])!=64):
        raise ValueError('original-law rehearsal requires its exact discarded parent pool')
    rows=pool['candidate_examples'];worlds=pool['private_worlds']
    original=set(SECONDARY_BY_ROLE);known=original|set(SECONDARY_BY_ROLE.values())
    keys=[r.get('key') for r in rows]
    if any(not isinstance(k,str) or not k for k in keys) or len(set(keys))!=64:
        raise ValueError('original-law rehearsal source keys are missing or duplicated')
    selected=[];excluded=[]
    for row in rows:
        lineage=row.get('lineages');raw=row.get('raw_record',{})
        if (not isinstance(lineage,list) or not lineage or lineage[0]!=row['key']
                or len(lineage)!=len(set(lineage)) or any(k not in worlds for k in lineage)
                or raw.get('domain') not in COUNTS):
            raise ValueError('original-law rehearsal lacks a complete declared example lineage')
        try:
            laws=[worlds[k]['state']['names']['law'] for k in lineage]
        except (KeyError,TypeError) as error:
            raise ValueError('original-law rehearsal source lacks actual law identity') from error
        if any(law not in known for law in laws):
            raise ValueError('original-law rehearsal contains an unknown law')
        if all(law in original for law in laws):selected.append(row)
        else:excluded.append({'key':row['key'],'reason':'secondary law in current or earlier work'})
    if dict(Counter(r['raw_record']['domain'] for r in selected))!=COUNTS:
        raise ValueError('original-law rehearsal complete eligible domain counts differ')
    assigned=mixture_keys(selected)
    if len(assigned)!=ASSIGNED:
        raise ValueError('original-law rehearsal assigned half differs')
    retained={key for row in selected for key in row['lineages']}
    return {'candidate_examples':copy.deepcopy(selected),
        'private_worlds':{key:copy.deepcopy(worlds[key]) for key in sorted(retained)},
        'split':'pilot','original_pool_sha256':pool['original_pool_sha256'],
        'original_law_selection':{'parent_pool_sha256':digest(pool),'rule':'retain every example whose current and all earlier works use original laws',
            'allowed_laws':sorted(original),'selected_keys':[r['key'] for r in selected],
            'excluded':excluded,'domain_counts':dict(COUNTS),'assigned_keys':sorted(assigned),
            'assigned_sources':ASSIGNED,'selection_uses_reader_or_future_outcome':False,
            'scope':'already exposed discarded timing pool; no scientific fit or admission'}}
