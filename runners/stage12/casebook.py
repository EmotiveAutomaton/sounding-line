"""Bundle complete source-bound provider cases without selecting their outcomes.

DESIGN CHECK: LESSONS 2-5; READER_HEURISTICS 9-10. NULL: all-unknown earns
no useful yield; an oracle stays a control. ALTERNATIVE: completed evidence
supports a usable case without admitting its hypotheses as human truth. Changed
terminal bytes, missing source members or invalid anchors refuse packaging.
Every case is selected by a frozen source roster, never by scientific scores.
"""
from .common import read, freeze, filehash, digest
import json
from .provider import validate, packet, metrics


def git_baseline_packets(directory):
    """Preserve exact recorded-change/unknown output, with file-level scope."""
    requests=read(directory/'REQUESTS.json')
    targets={r['id']:r for r in read(directory/'EVALUATOR_ONLY.json')}
    cheap={(r['source_id'],r['view']):r for r in read(directory/'CHEAP_BASELINE.json')}
    labels=('create','modify','delete','rename','copy','unknown')
    packets=[]
    for row in requests:
        if row['method']!='direct':
            continue
        # The unadapted request has one fixed instruction line before evidence.
        text=row['request']['messages'][-1]['content']
        prefix,text=text.split('\n',1)
        if prefix!='Give a short evidence-based explanation.':
            raise ValueError('unreviewed Git baseline request wrapper')
        evidence=json.JSONDecoder().raw_decode(text)[0]['evidence']
        baseline=cheap[(row['source_id'],row['direction'])]
        predicted=labels[max(range(6),key=baseline['probabilities'].__getitem__)]
        truth_label=labels[max(range(6),key=targets[row['id']]['target'].__getitem__)]
        captured=evidence['current_bytes'] or ''
        anchors=[dict(id='file',start=0,end=len(captured))] if captured else []
        located=bool(anchors)
        truth=[dict(slot='file-operation',operation=truth_label,actor='constructed Git fixture',relation='recorded-change',
                    span_state='located' if located else 'unknown',span_ids=['file'] if located else [])]
        observed=predicted!='unknown'
        claim=dict(truth[0],id='operation',role='process',operation=predicted,status='observed' if observed else 'unobserved',
            span_state=truth[0]['span_state'] if observed else 'unknown',span_ids=truth[0]['span_ids'] if observed else [],
            evidence_refs=['parent-relative-record'] if observed else [],support='recorded file operation; no subfile or mental claim')
        tier={'endpoint':'E0','endpoint-diff':'E2','endpoint-diff-message':'E2'}[row['direction']]
        p=packet(row['id'],dict(endpoint=captured,anchors=anchors,source_public=evidence),baseline['method'],[claim],
                 tier=tier,origin='constructed Git fixture; exact extraction control')
        p['next_discriminator']='The missing parent-relative change record; a goal claim additionally requires an independent target record.'
        p['correspondence_audit']=metrics([claim],truth)
        p['location_scope']='whole-file operation only; an absent deleted endpoint has no captured passage'
        packets.append(p)
    if len(packets)!=len(cheap):
        raise ValueError('incomplete cheap Git provider roster')
    return packets


def run(out, card, pulse, raw):
    packets, index, inputs = [], [], []
    roles = set()
    for source in card['sources']:
        directory = raw/'jobs'/source['job']
        terminal = read(directory/'COMPLETE.json')
        if terminal['status']!='complete' or filehash(directory/'COMPLETE.json')!=source['terminal_sha256']:
            raise ValueError('case source terminal changed')
        for name, expected in terminal['output_files'].items():
            if filehash(directory/name)!=expected:
                raise ValueError('case source output changed')
        rows = git_baseline_packets(directory) if source.get('adapter')=='git-baseline' else read(directory/source.get('file','PACKETS.json'))
        recorded_metrics = read(directory/'METRICS.json') if (directory/'METRICS.json').exists() else []
        by_metric = {(r['case_id'],r['tier'],r['method']):r for r in recorded_metrics}
        if not rows:
            raise ValueError('empty provider source')
        for ordinal, original in enumerate(rows):
            validate(original)
            anchors = original['artifact']['anchors']
            if len({a['id'] for a in anchors})!=len(anchors):
                raise ValueError('duplicate capture anchor')
            key = digest([source['job'],ordinal,original])
            tier = original['analysis']['evidence_tier']
            own_roles = {'E0':'artifact-only','E1':'added-context','E2':'witnessed-process',
                'E2-full':'witnessed-process','E2-sparse':'witnessed-process','E1-corrected':'added-context','O':'oracle-control'}
            packet_roles = {own_roles[tier]}
            if source.get('reference_only') or tier=='O':
                packet_roles.add('oracle-control')
            if source.get('cheap_baseline') and (tier in ('E0','E1') or source.get('adapter')=='git-baseline'):
                packet_roles.add('cheap-baseline-output')
            if original.get('compatible_processes') or all(c['status']=='unobserved' for c in original['claims']):
                packet_roles.add('ambiguity-or-unknown')
            roles.update(packet_roles)
            snapshot = original.get('maker_snapshot') or dict(id=digest([original['case_id'],original['capture']]),
                scope='dated source evidence snapshot; not independently validated persistent human preferences')
            audit = original.get('correspondence_audit')
            if audit is None:
                audit = by_metric.get((original['case_id'],tier,original['analysis']['method']))
            if audit is None and original.get('model_valid') is not False:
                raise ValueError('case lacks bound correspondence metrics')
            # An invalid reading retains its source and failure, never fabricated
            # zero loss or a favorable coverage denominator.
            metric_state = 'recorded' if audit is not None else 'invalid reading; metrics unavailable'
            packets.append(dict(id=key, provider_packet=original, maker_snapshot=snapshot,
                source_receipt=dict(job=source['job'],terminal_sha256=source['terminal_sha256'],ordinal=ordinal),
                roles=sorted(packet_roles), selection='all packets in prospectively named complete source files',
                scientific_status=source['scientific_status'],
                correspondence_metrics=audit, metric_state=metric_state,
                next_discriminator=original['next_discriminator'],
                claim_classes={s:[c['id'] for c in original['claims'] if c['status']==s]
                              for s in ('observed','inferred','contradicted','unobserved')},
                unknown_targets=['governing purpose without independent target evidence','adoption','stable maker values']))
            index.append(dict(id=key, source_job=source['job'], ordinal=ordinal, roles=sorted(packet_roles),
                method=original['analysis']['method'], evidence_tier=tier, maker_snapshot=snapshot['id']))
        inputs.append(dict(job=source['job'], terminal_sha256=source['terminal_sha256'], packets=len(rows)))
        pulse(phase='casebook-source-binding', completed=len(inputs), total=len(card['sources']))
    required={'artifact-only','added-context','witnessed-process','oracle-control','ambiguity-or-unknown','cheap-baseline-output'}
    if not required<=roles:
        raise ValueError('missing case role: '+str(sorted(required-roles)))
    null_source=next(s for s in card['sources'] if s.get('null_controls'))
    null=read(raw/'jobs'/null_source['job']/'CONSTRUCTED_NULL.json')
    if null['unknown_metrics']['supported_useful_events']!=0 or null['wrong_location_metrics']['correctly_located_useful_events']!=0:
        raise ValueError('casebook known-answer control failed')
    freeze(out/'PACKETS.json', packets);freeze(out/'INDEX.json', index)
    freeze(out/'CONSTRUCTED_NULL.json', null)
    freeze(out/'SOURCE_BINDINGS.json', inputs)
    return dict(status='complete',kind='infrastructure',packets=len(packets),source_files=len(inputs),case_roles=sorted(roles),
        scope='Private source-bound ToMpathy provider bundle; no frontend, new inference or scientific admission',
        controls=dict(complete_sources=True,all_roles=True,anchors_valid=True,unknown_not_useful=True,mislocated_not_useful=True),
        files={n:filehash(out/n) for n in ('PACKETS.json','INDEX.json','CONSTRUCTED_NULL.json','SOURCE_BINDINGS.json')})
