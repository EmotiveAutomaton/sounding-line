"""Cloud-only common naming memory, selected before either naming condition.

DESIGN CHECK: LESSONS3-5. Both hypotheses retain identical ordered definitions,
numeric support and whole episodes. Pack the fully serialized grounded wrapper
and reserve feedback first; the opaque view removes descriptions only.
"""
from copy import deepcopy
import math
from . import reading_memory as memory, reading_proposal as proposal
from .reader import from_record, tokens
from .contracts import canonical,digest

FEEDBACK_BYTES=4096
SCOPE='training/prior-artifact reconstructions, not the maker\'s known procedures'


def paired_representation(task,envelope,training,answers,library,profile,naming):
    if naming not in {'opaque','grounded'}: raise ValueError('unknown cloud naming condition')
    truth=memory.joined(training,answers)
    if task.task_id in truth: raise ValueError('target overlaps training')
    base=proposal.request_for(task,envelope,profile=profile)
    cap=min(memory.STORE_BYTES,16384-sum(len(x['content'].encode('utf8')) for x in base['messages'])-384-512-FEEDBACK_BYTES-128)
    rep={'procedures':memory.representation(library,'grounded'),'episodes':[],'scope':SCOPE}
    if len(canonical(rep).encode('utf8'))>cap:
        raise ValueError('common procedure wrapper cannot fit both naming conditions')
    query=tokens(task.evidence);ranked=[]
    for row in training:
        source=from_record(row);count=tokens(source.evidence)
        norm=math.sqrt(sum(v*v for v in query.values())*sum(v*v for v in count.values()))
        similarity=sum(v*count.get(k,0) for k,v in query.items())/norm if norm else 0
        ranked.append((-similarity,source.task_id,source))
    ids=[];skipped=[]
    for _,identifier,source in sorted(ranked):
        episode={'evidence_view':source.evidence_view,'evidence':source.evidence,
                 'question':source.question,'observed_outcome':dict(source.choices)[truth[identifier]['correct_choice']]}
        candidate={**rep,'episodes':rep['episodes']+[episode]}
        if len(canonical(candidate).encode('utf8'))>cap:
            skipped.append(identifier);continue
        rep=candidate;ids.append(identifier)
        if len(ids)==memory.MAX_EXAMPLES:break
    common=digest(rep);grounded_bytes=len(canonical(rep).encode('utf8'))
    if naming=='opaque':
        rep=deepcopy(rep)
        rep['procedures']=[{k:v for k,v in p.items() if k!='description'} for p in rep['procedures']]
    proposal.request_for(task,envelope,memory=rep,profile=profile)
    return rep,{'selected_ids':ids,'size_skipped_ids':skipped,'common_grounded_sha256':common,
                'common_grounded_bytes':grounded_bytes,'effective_store_limit_bytes':cap,
                'reserved_feedback_bytes':FEEDBACK_BYTES,'actual_store_bytes':len(canonical(rep).encode('utf8'))}
