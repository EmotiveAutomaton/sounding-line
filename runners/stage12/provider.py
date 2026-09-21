"""One minimal ToMpathy concept adapter, with no frontend or inferred percentages.

DESIGN CHECK: LESSONS 2-5; READER_HEURISTICS 9-10. NULL: all unknown earns no
useful located yield. ALTERNATIVE: a supported operation at the wrong passage
does not count as correctly located. Recorded selection never licenses mental
review, endorsement, governing purpose or stable human values.
"""
from __future__ import annotations
from .common import digest

SCHEMA='soundingline.provider.1'
STATUS={'observed','inferred','contradicted','unobserved'}
ROLES={'G','g_t','C_ext','adoption','process','maker_value'}

def packet(case_id,evidence,method,claims,alternatives=(),*,tier='E0',origin='imported'):
    result=dict(schema=SCHEMA,case_id=case_id,artifact=dict(revision=digest(evidence.get('endpoint','')),
        text=evidence.get('endpoint',''),anchors=evidence.get('anchors',[])),
        capture=dict(source_sha256=digest(evidence),origin=origin),
        analysis=dict(method=method,evidence_tier=tier,evidence_scope=evidence),
        claims=claims,compatible_processes=list(alternatives),
        goals=[dict(role=r,status='unobserved',value=None,support=None) for r in ('G','g_t','C_ext','adoption')],
        maker_values=dict(status='unobserved',value=None),
        support_semantics='support from declared evidence or uncalibrated candidate compatibility; no subjective percentages',
        next_discriminator='A timestamped choice/operation record linked to this passage; goals additionally need an independent target record.')
    validate(result);return result

def validate(p):
    if p['schema']!=SCHEMA:raise ValueError('provider version')
    anchors={a['id'] for a in p['artifact']['anchors']}
    n=len(p['artifact']['text'])
    for a in p['artifact']['anchors']:
        if not 0<=a['start']<=a['end']<=n:raise ValueError('anchor outside captured revision')
    for c in p['claims']:
        if c['status'] not in STATUS or c['role'] not in ROLES:raise ValueError('untyped claim')
        if not set(c.get('span_ids',[]))<=anchors:raise ValueError('claim refers to absent passage')
        if c['status']=='observed' and not c.get('evidence_refs'):raise ValueError('observed claim lacks record')
        if c['role'] in ('G','g_t','adoption','maker_value') and c['status']=='observed' and not c.get('independent_target_record'):
            raise ValueError('operation upgraded to a mental target')
    if p['maker_values']['status']=='unobserved' and p['maker_values']['value'] is not None:
        raise ValueError('unknown value is not a fabricated zero')
    return True

def metrics(claims,truth):
    """Exact declared operation opportunities, including absent/unknown claims."""
    by={r['slot']:r for r in truth};located=0;correct=0;unsupported=0;covered=0
    for c in claims:
        if c['role']!='process' or c['status']=='unobserved':continue
        t=by.get(c['slot']);covered+=1
        ok=t is not None and all(c.get(k)==t.get(k) for k in ('operation','actor','relation'))
        if ok and t['operation']!='absent':
            correct+=1
            located+=int(c.get('span_state')==t.get('span_state')=='located'
                         and set(c.get('span_ids',[]))==set(t.get('span_ids',[])))
        if not ok:unsupported+=1
    return dict(eligible_event_denominator=len(truth),covered_opportunities=covered,
        supported_useful_events=correct,correctly_located_useful_events=located,
        unsupported_operation_claims=unsupported,unknown_opportunities=len(truth)-covered,
        unsupported_mental_assertions=sum(c['role'] in ('G','g_t','adoption','maker_value') and c['status']=='observed'
                                         and not c.get('independent_target_record') for c in claims))

def claims_from_facts(facts,*,observed=False):
    from runners.stage11_1.models import FIELDS
    out=[]
    for f in facts:
        values={k:labels[max(range(len(f[k])),key=f[k].__getitem__)] if isinstance(f[k],list) else f[k]
                for k,labels in FIELDS.items()}
        status='unobserved' if values['operation'] in ('unknown','absent') else 'observed' if observed else 'inferred'
        out.append(dict(id=f['slot'],slot=f['slot'],role='process',status=status,**values,
            span_ids=f.get('span_ids',[]),span_state=f.get('span_state','unknown'),
            evidence_refs=['source-operation:'+f['slot']] if observed else [],
            support='record-backed' if observed else 'uncalibrated hypothesis' if status=='inferred' else None))
    return out
